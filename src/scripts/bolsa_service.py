from __future__ import annotations
import asyncio
import logging
import traceback
import time
from flask import current_app
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .bot_page_manager import get_page
from .bot_login import auto_login, LoginError, TARGET_DATA_PAGE_URL, LOGIN_PAGE_URL_FRAGMENT
from .bot_data_capture import capture_market_time, capture_premium_data_via_network, validate_premium_data, DataCaptureError
from src.utils.db_io import store_prices_in_db
from src.extensions import socketio
from src.routes.errors import log_error
from src.utils.page_utils import _ensure_target_page

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

# --- INICIO DE CORRECCIÓN ---

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
    # Usamos wait_for_load_state para asegurarnos de que la página termina de cargar
    # antes de que los timeouts de los listeners expiren.
    await page.reload(wait_until="domcontentloaded", timeout=30000)

    # Esperar por las tareas de captura de datos.
    market_time, raw_data = await asyncio.gather(time_task, data_task)
    
    return market_time, raw_data

async def run_bolsa_bot(app=None, username=None, password=None, **kwargs) -> str | None:
    global _is_first_run_since_startup
    
    try:
        await asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)
    except asyncio.TimeoutError:
        return "ignored_already_running"
    
    try:
        logger.info(f"=== INICIO DE EJECUCIÓN (Primera vez: {_is_first_run_since_startup}) ===")
        page = await get_page()

        if _is_first_run_since_startup:
            logger.info("🚀 Fase 1: Establecimiento de Sesión Inicial.")
            await perform_session_health_check(page, username, password)
            _is_first_run_since_startup = False
            socketio.emit("initial_session_ready")
            # En el primer run, el frontend inicia la fase 2.
            # Aquí la corrección es que si el primer run es automático, debería continuar
            if not kwargs.get('is_manual_trigger', True):
                 logger.info("El primer run fue automático, procediendo a Fase 2.")
            else:
                return "phase_1_complete"

        logger.info("🎬 Fase 2: Captura de Datos.")
        await perform_session_health_check(page, username, password)

        if not await _ensure_target_page(page, logger):
             raise DataCaptureError("No se pudo asegurar la página de destino para la captura.")

        # --- Lógica de Reintentos ---
        max_attempts = 3
        market_time, raw_data = None, None
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"--- Intento de captura {attempt}/{max_attempts} ---")
            try:
                market_time, raw_data = await _attempt_data_capture(page)
                
                # Si ambos datos se capturan, salimos del bucle
                if market_time and raw_data:
                    logger.info(f"✓ Captura exitosa en el intento {attempt}.")
                    break
                
                # Si falta alguno, lo registramos y preparamos para el reintento
                missing = []
                if not market_time: missing.append("hora del mercado")
                if not raw_data: missing.append("datos de precios")
                logger.warning(f"Intento {attempt} fallido. Faltan datos: {', '.join(missing)}.")
                
            except Exception as e:
                logger.error(f"Error grave en el intento de captura {attempt}: {e}", exc_info=True)

            # Si no fue el último intento, esperamos antes de reintentar
            if attempt < max_attempts:
                wait_time = attempt * 2  # Espera exponencial: 2s, 4s
                logger.info(f"Esperando {wait_time} segundos antes del próximo intento...")
                await asyncio.sleep(wait_time)
            else:
                 logger.error("Se agotaron los reintentos de captura.")

        # --- Fin Lógica de Reintentos ---

        if not market_time:
            raise DataCaptureError("No se pudo interceptar la hora del mercado después de varios intentos.")
        if not raw_data:
            raise DataCaptureError("No se pudo interceptar los datos de precios después de varios intentos.")
        
        if not validate_premium_data(raw_data):
            raise DataCaptureError("Formato de datos no válido.")
        
        logger.info("✓ Hora y datos capturados. Pasando a la base de datos...")
        
        with (app or current_app).app_context():
            store_prices_in_db(raw_data, market_time, app=app)
            
        return "phase_2_complete"

    except Exception as e:
        # Resetear el estado si el bot falla para que el próximo intento sea un "primer run" completo
        if isinstance(e, (LoginError, DataCaptureError)):
            _is_first_run_since_startup = True 
        logger.error(f"Error en la ejecución del bot: {e}", exc_info=True)
        socketio.emit("bot_error", {"message": str(e)})
        with (app or current_app).app_context(): log_error("bot_automation", str(e), traceback.format_exc())
        return f"error: {e}"
    finally:
        if _bot_running_lock.locked():
             _bot_running_lock.release()
        logger.info("=== FIN DE EJECUCIÓN ===")

# --- FIN DE CORRECCIÓN ---