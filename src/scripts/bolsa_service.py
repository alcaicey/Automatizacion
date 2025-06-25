from __future__ import annotations
import asyncio
import logging
import traceback
import time
from datetime import datetime
from typing import List, Optional
from flask import current_app
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .bot_page_manager import get_page
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

async def check_if_logged_in(page: Page) -> bool:
    """
    Verifica si la sesión está activa comprobando la (in)visibilidad del botón de login.
    """
    logger.info("[Service] Verificando si existe una sesión activa...")
    
    # El botón de login tiene el ID 'menuppal-login' y solo se muestra si NO hay sesión.
    login_button = page.locator('#menuppal-login')
    
    try:
        # Usamos un timeout corto. Si el botón de login es visible, significa que NO estamos logueados.
        await login_button.wait_for(state="visible", timeout=5000)
        logger.warning("[Service] Botón de 'Ingresar' encontrado. No hay sesión activa.")
        return False
    except TimeoutError:
        # Si el botón de login NO es visible después de 5 segundos, es una señal fuerte
        # de que ya estamos logueados (porque en su lugar se muestra el perfil del usuario).
        logger.info("[Service] ✓ No se encontró el botón de 'Ingresar'. Se asume sesión activa.")
        return True

async def perform_session_health_check(page: Page, username: str, password: str) -> None:
    """
    Verifica la salud de la sesión desde la página principal y fuerza un re-login si es necesario.
    """
    logger.info("[Health Check] Verificando estado de la sesión...")
    
    # 1. SIEMPRE vamos a la página principal primero para un chequeo limpio.
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
    
    # 2. Comprobamos si estamos logueados desde la página principal.
    is_logged_in = await check_if_logged_in(page)
    
    # 3. Si no lo estamos, llamamos a nuestro robusto auto_login.
    if not is_logged_in:
        logger.warning("[Health Check] Sesión no válida o expirada. Forzando re-login...")
        await auto_login(page, username, password)
        
        # 4. Verificación final post-login.
        await page.goto(TARGET_DATA_PAGE_URL, wait_until="domcontentloaded", timeout=20000)
        premium_badge = page.locator("span.badge:has-text('Tiempo Real')")
        try:
            await premium_badge.wait_for(state="visible", timeout=10000)
            logger.info("[Health Check] ✓ Re-login exitoso y verificado en la página de datos.")
        except TimeoutError:
            raise LoginError("El re-login forzado falló. No se pudo acceder a la página de datos premium.")
    else:
        logger.info("[Health Check] ✓ La sesión existente es válida.")

async def _attempt_data_capture(page: Page) -> tuple[datetime | None, dict | None]:
    """
    Función interna que realiza un único intento de captura de datos.
    """
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
    
    try:
        logger.info(f"=== INICIO DE EJECUCIÓN DEL BOT (Primera vez: {_is_first_run_since_startup}) ===")
        page = await get_page()

        logger.info("🚀 Fase 1: Chequeo y establecimiento de Sesión.")
        await perform_session_health_check(page, username, password)
        
        if _is_first_run_since_startup:
            _is_first_run_since_startup = False
            socketio.emit("initial_session_ready")
            logger.info("✓ Navegador y sesión inicial listos. Notificación enviada al frontend.")

        logger.info("🎬 Fase 2: Captura de Datos de Precios de Acciones.")
        
        if not await _ensure_target_page(page, logger):
             raise DataCaptureError("No se pudo asegurar la página de destino para la captura de acciones.")

        max_attempts = 3
        market_time, raw_data = None, None
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"--- Intento de captura de acciones {attempt}/{max_attempts} ---")
            try:
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

            if attempt < max_attempts:
                await asyncio.sleep(attempt * 2)
            else:
                 logger.error("Se agotaron los reintentos de captura de acciones.")
        
        if not market_time:
            logger.warning("No se pudo interceptar la hora del mercado en tiempo real. Calculando hora de cierre de fallback.")
            market_time = get_fallback_market_time()
            logger.info(f"✓ Usando hora de fallback: {market_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        if not raw_data:
            raise DataCaptureError("No se pudieron capturar los datos de precios después de varios intentos.")
        
        if not validate_premium_data(raw_data):
            raise DataCaptureError("El formato de los datos de acciones no es válido.")
        
        logger.info(f"✓ Datos de acciones capturados. Se usarán con el timestamp: {market_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
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