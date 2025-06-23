from __future__ import annotations
import asyncio
import logging
import traceback
import time
from datetime import datetime
from flask import current_app
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# --- Lógica del Bot ---
from .bot_page_manager import get_page
from .bot_login import auto_login, LoginError, TARGET_DATA_PAGE_URL
from .bot_data_capture import capture_market_time, capture_premium_data_via_network, validate_premium_data, DataCaptureError

# --- Utilidades y Extensiones ---
from src.utils.db_io import store_prices_in_db, save_filtered_comparison_history
from src.extensions import socketio
from src.routes.errors import log_error
from src.utils.page_utils import _ensure_target_page
from src.utils.time_utils import get_fallback_market_time # <-- IMPORTACIÓN NUEVA

logger = logging.getLogger(__name__)
_bot_running_lock = asyncio.Lock()
_is_first_run_since_startup = True

async def check_if_logged_in(page: Page) -> bool:
    logger.info("[Service] Verificando si existe una sesión activa en la página actual...")
    try:
        await page.locator("span.badge:has-text('Tiempo Real')").first.wait_for(state="visible", timeout=10000)
        logger.info("[Service] ✓ Sesión activa encontrada (indicador 'Tiempo Real').")
        return True
    except PlaywrightTimeoutError:
        logger.warning("[Service] No se encontró indicador de sesión activa.")
        return False

async def perform_session_health_check(page: Page, username: str, password: str) -> None:
    """
    Verifica la salud de la sesión. Si no es válida, fuerza un re-login.
    """
    logger.info("[Health Check] Verificando estado de la sesión...")
    await page.goto(TARGET_DATA_PAGE_URL, wait_until="domcontentloaded", timeout=20000)
    
    is_logged_in = await check_if_logged_in(page)
    
    if not is_logged_in:
        logger.warning("[Health Check] Sesión no válida. Forzando re-login...")
        await auto_login(page, username, password)
        if not await check_if_logged_in(page):
            raise LoginError("El re-login forzado falló.")
        logger.info("[Health Check] ✓ Re-login exitoso, sesión renovada.")
    else:
        logger.info("[Health Check] ✓ La sesión existente es válida.")

async def _attempt_data_capture(page: Page) -> tuple[datetime | None, dict | None]:
    """
    Función interna que realiza un único intento de captura de datos.
    Separa la lógica de captura para poder reintentarla.
    """
    logger.info("Preparando captura concurrente y recarga de página...")
    
    # Iniciar las tareas de escucha
    time_task = asyncio.create_task(capture_market_time(page, logger))
    data_task = asyncio.create_task(capture_premium_data_via_network(page, logger))
    
    # Darle un instante a los listeners para que se registren
    await asyncio.sleep(0.1)

    # Disparar la recarga de la página
    logger.info("Disparando recarga de página...")
    await page.reload(wait_until="domcontentloaded", timeout=30000)

    # Esperar por las tareas de captura de datos.
    market_time, raw_data = await asyncio.gather(time_task, data_task)
    
    return market_time, raw_data

async def run_bolsa_bot(app=None, username=None, password=None, **kwargs) -> str | None:
    global _is_first_run_since_startup
    
    # Adquirir el lock para evitar ejecuciones concurrentes
    try:
        await asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)
    except asyncio.TimeoutError:
        logger.warning("Se ignoró una nueva solicitud de ejecución del bot porque ya estaba en curso.")
        return "ignored_already_running"
    
    try:
        logger.info(f"=== INICIO DE EJECUCIÓN DEL BOT (Primera vez: {_is_first_run_since_startup}) ===")
        page = await get_page()

        # --- FASE 1: Asegurar Sesión ---
        # Siempre se realiza un chequeo de salud de la sesión
        logger.info("🚀 Fase 1: Chequeo y establecimiento de Sesión.")
        await perform_session_health_check(page, username, password)
        
        # Si era la primera ejecución, notificamos al frontend que el navegador está listo.
        if _is_first_run_since_startup:
            _is_first_run_since_startup = False
            socketio.emit("initial_session_ready")
            logger.info("✓ Navegador y sesión inicial listos. Notificación enviada al frontend.")

        # --- FASE 2: Captura de Datos de Acciones ---
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
                await asyncio.sleep(attempt * 2) # Espera incremental
            else:
                 logger.error("Se agotaron los reintentos de captura de acciones.")
        
        # --- INICIO DE LA MODIFICACIÓN: Lógica de Fallback para la Hora del Mercado ---
        if not market_time:
            logger.warning("No se pudo interceptar la hora del mercado en tiempo real. Calculando hora de cierre de fallback.")
            market_time = get_fallback_market_time()
            logger.info(f"✓ Usando hora de fallback: {market_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        if not raw_data:
            # Si después de los reintentos no hay datos de precios, es un error fatal.
            raise DataCaptureError("No se pudieron capturar los datos de precios después de varios intentos.")
        # --- FIN DE LA MODIFICACIÓN ---
        
        if not validate_premium_data(raw_data):
            raise DataCaptureError("El formato de los datos de acciones no es válido.")
        
        logger.info(f"✓ Datos de acciones capturados. Se usarán con el timestamp: {market_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Guardar en la DB dentro del contexto de la app
        with (app or current_app).app_context():
            store_prices_in_db(raw_data, market_time, app=app)
            save_filtered_comparison_history(market_timestamp=market_time, app=app)
            
        return "update_complete"

    except Exception as e:
        # Si algo falla (login, captura, etc.), reseteamos el flag para que el próximo intento sea completo.
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