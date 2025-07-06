# src/scripts/bolsa_service.py

from __future__ import annotations
import asyncio
import logging
import traceback
import time
import random
from datetime import datetime
from typing import List, Optional
from flask import current_app
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from .bot_page_manager import get_page, recreate_page
from .bot_login import auto_login, LoginError, TARGET_DATA_PAGE_URL, BASE_URL
from .bot_data_capture import capture_market_time, capture_premium_data_via_network, validate_premium_data, DataCaptureError
from src.utils.db_io import store_prices_in_db, save_filtered_comparison_history
from src.extensions import socketio
from src.routes.errors import log_error
from src.utils.page_utils import _ensure_target_page
from src.utils.time_utils import get_fallback_market_time

logger = logging.getLogger(__name__)
_bot_running_lock = asyncio.Lock()
_is_first_run_since_startup = True

def is_bot_running():
    """Devuelve True si el lock asíncrono del bot está tomado."""
    return _bot_running_lock.locked()

async def check_if_logged_in(page: Page) -> bool:
    logger.info("[Service] Verificando si existe una sesión activa...")
    if "validate.perfdrive.com" in page.url or "radware" in page.url:
        logger.error("[Service] ¡Página de CAPTCHA detectada! Se considera sesión como NO activa.")
        return False
    profile_element = page.locator('div[ng-show="globales.miperfil.activo"]')
    try:
        await profile_element.wait_for(state="visible", timeout=5000)
        logger.info("[Service] ✓ Elemento de perfil de usuario encontrado. Sesión activa confirmada.")
        return True
    except PlaywrightTimeoutError:
        logger.warning("[Service] No se encontró el elemento de perfil de usuario. Se asume que no hay sesión activa.")
        return False

async def perform_session_health_check(page: Page, username: str, password: str) -> Page:
    logger.info("[Health Check] Verificando estado de la sesión...")
    try:
        await page.goto(BASE_URL, wait_until="load", timeout=60000)
    except PlaywrightError as e:
        if "Target page, context or browser has been closed" in str(e):
            logger.warning("[Health Check] La página fue cerrada antes del chequeo. Recreando...")
            page = await recreate_page()
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        else:
            logger.error(f"[Health Check] Timeout al intentar navegar a la página principal: {e}")
            raise LoginError("Timeout al navegar a la página principal durante health check.")
    
    is_logged_in = await check_if_logged_in(page)
    
    if not is_logged_in:
        logger.warning("[Health Check] Sesión no válida o expirada. Forzando re-login...")
        page = await auto_login(page, username, password)
        if not page:
            raise LoginError("El proceso de auto-login falló después de múltiples reintentos.")
    else:
        logger.info("[Health Check] ✓ La sesión existente es válida.")
    
    # --- INICIO DE LA MODIFICACIÓN CLAVE ---
    # Después de asegurar el login, SIEMPRE navegar a la página de datos.
    logger.info(f"[Health Check] Navegando explícitamente a la página de datos: {TARGET_DATA_PAGE_URL}")
    await page.goto(TARGET_DATA_PAGE_URL, wait_until="domcontentloaded", timeout=20000)
    premium_badge = page.locator("span.badge:has-text('Tiempo Real')")
    try:
        await premium_badge.wait_for(state="visible", timeout=10000)
        logger.info("[Health Check] ✓ Verificado en la página de datos premium.")
    except PlaywrightTimeoutError:
        raise LoginError("No se pudo verificar el acceso a la página de datos premium después del login/health check.")
    # --- FIN DE LA MODIFICACIÓN CLAVE ---
    
    return page

async def _attempt_data_capture(page: Page) -> tuple[datetime | None, dict | None]:
    logger.info("Preparando captura concurrente y recarga de página...")
    time_task = asyncio.create_task(capture_market_time(page, logger))
    data_task = asyncio.create_task(capture_premium_data_via_network(page, logger))
    await asyncio.sleep(0.1)
    logger.info("Disparando recarga de página...")
    await page.reload(wait_until="domcontentloaded", timeout=30000)
    market_time, raw_data = await asyncio.gather(time_task, data_task)
    return market_time, raw_data

async def run_bolsa_bot(app=None, username=None, password=None, filtered_symbols: Optional[List[str]] = None, **kwargs) -> str | None:
    global _is_first_run_since_startup
    
    try:
        await asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)
    except asyncio.TimeoutError:
        logger.warning("Se ignoró una nueva solicitud de ejecución del bot porque ya estaba en curso.")
        return "ignored_already_running"
    
    page = None
    try:
        logger.info(f"=== INICIO DE EJECUCIÓN DEL BOT (Primera vez: {_is_first_run_since_startup}) ===")
        page = await get_page()
        
        logger.info("🚀 Fase 1: Chequeo y establecimiento de Sesión.")
        page = await perform_session_health_check(page, username, password)
        
        if _is_first_run_since_startup:
            _is_first_run_since_startup = False
            socketio.emit("initial_session_ready")
            logger.info("✓ Navegador y sesión inicial listos. Notificación enviada al frontend.")

        logger.info("🎬 Fase 2: Captura de Datos de Precios de Acciones.")
        
        # La verificación de _ensure_target_page ahora es una doble seguridad,
        # pero la navegación principal ocurre en perform_session_health_check.
        if not await _ensure_target_page(page, logger):
             raise DataCaptureError("No se pudo asegurar la página de destino para la captura de acciones.")

        max_attempts = 3
        market_time, raw_data = None, None
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"--- Intento de captura de acciones {attempt}/{max_attempts} ---")
            try:
                if not page or page.is_closed():
                    logger.warning("[Capture] La página fue cerrada. Recreando y navegando a la página de datos...")
                    page = await recreate_page()
                    await page.goto(TARGET_DATA_PAGE_URL, wait_until="domcontentloaded", timeout=20000)

                market_time, raw_data = await _attempt_data_capture(page)
                
                if market_time and raw_data:
                    logger.info(f"✓ Captura de acciones exitosa en el intento {attempt}.")
                    break
                
                missing = []
                if not market_time: missing.append("hora del mercado")
                if not raw_data: missing.append("datos de precios")
                logger.warning(f"Intento de captura de acciones {attempt} fallido. Faltan datos: {', '.join(missing)}.")
                
            except Exception as e:
                logger.error(f"Error grave en el intento de captura de acciones {attempt}: {e}", exc_info=True)
                page = None # Forzar recreación en el siguiente intento

            if attempt < max_attempts:
                await asyncio.sleep(attempt * 2)
            else:
                 logger.error("Se agotaron los reintentos de captura de acciones.")
        
        if not market_time:
            logger.warning("No se pudo interceptar la hora del mercado. Usando hora de fallback.")
            market_time = get_fallback_market_time()
            logger.info(f"✓ Usando hora de fallback: {market_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        if not raw_data:
            raise DataCaptureError("No se pudieron capturar los datos de precios después de varios intentos.")
        
        if not validate_premium_data(raw_data):
            raise DataCaptureError("El formato de los datos de acciones no es válido.")
        
        logger.info(f"✓ Datos de acciones capturados. Timestamp: {market_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        with (app or current_app).app_context():
            store_prices_in_db(raw_data, market_time, app=app, filtered_symbols=filtered_symbols)
            save_filtered_comparison_history(market_timestamp=market_time, app=app)
            
        return "update_complete"

    except Exception as e:
        if isinstance(e, (LoginError, DataCaptureError)):
            _is_first_run_since_startup = True 
        
        error_message = f"Error crítico en la ejecución del bot: {str(e)}"
        logger.error(error_message, exc_info=True)
        socketio.emit("bot_error", {"message": str(e)})
        with (app or current_app).app_context():
            log_error("bot_automation", str(e), traceback.format_exc())
        return f"error: {e}"
        
    finally:
        if _bot_running_lock.locked():
             _bot_running_lock.release()
        logger.info("=== FIN DE EJECUCIÓN DEL BOT ===")