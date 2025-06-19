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
    # ... (sin cambios)
    pass

# --- INICIO DE CORRECCIÓN: Estrategia "Health Check" ---
async def perform_session_health_check(page: Page) -> bool:
    """
    Navega a una página protegida para verificar si la sesión sigue activa.
    Devuelve True si la sesión está viva, False si ha expirado.
    """
    logger.info("[Health Check] Verificando estado de la sesión...")
    health_check_url = "https://www.bolsadesantiago.com/plus_portafolio"
    try:
        await page.goto(health_check_url, wait_until="domcontentloaded", timeout=20000)
        
        # Si la URL actual contiene la URL de login, la sesión ha expirado.
        if LOGIN_PAGE_URL_FRAGMENT in page.url:
            logger.warning("[Health Check] Sesión expirada: Redirección a página de login detectada.")
            return False
        
        # Si no fuimos redirigidos, la sesión está activa.
        logger.info("[Health Check] ✓ Sesión activa confirmada.")
        return True
    except PlaywrightTimeoutError:
        logger.error("[Health Check] Timeout durante la verificación de sesión. Asumiendo que expiró.")
        return False
# --- FIN DE CORRECCIÓN ---


async def force_relogin(page: Page, username: str, password: str):
    """Fuerza un nuevo proceso de login."""
    logger.warning("Forzando re-login para renovar la sesión...")
    # Asegurarnos de estar en la página de datos antes de intentar el login
    await page.goto(TARGET_DATA_PAGE_URL, wait_until="networkidle")
    
    # auto_login ahora devuelve una tupla, pero solo nos interesa el éxito aquí.
    login_success, _ = await auto_login(page, username, password)
    
    if not login_success:
        raise LoginError("El re-login forzado ha fallado durante el proceso de auto_login.")

    await page.wait_for_url(f"**{TARGET_DATA_PAGE_URL}**", timeout=45000)
    
    if not await check_if_logged_in(page):
        raise LoginError("Re-login pareció exitoso, pero no se encontró indicador de sesión activa post-login.")
    
    logger.info("✓ Re-login forzado completado exitosamente.")


async def run_bolsa_bot(app=None, username=None, password=None, **kwargs) -> str | None:
    global _is_first_run_since_startup
    
    try:
        await asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)
    except asyncio.TimeoutError:
        return "ignored_already_running"
    
    try:
        logger.info(f"=== INICIO DE EJECUCIÓN (Primera vez: {_is_first_run_since_startup}) ===")
        page = await get_page()

        # --- INICIO DE CORRECCIÓN: Lógica de Health Check ---
        session_is_active = await perform_session_health_check(page)

        if _is_first_run_since_startup or not session_is_active:
            if _is_first_run_since_startup:
                logger.info("🚀 Fase 1: Establecimiento de Sesión Inicial.")
            else:
                logger.warning("La sesión ha caducado. Forzando re-login.")
            
            await force_relogin(page, username, password)
            is_first_run_flag = _is_first_run_since_startup
            _is_first_run_since_startup = False
            
            if is_first_run_flag:
                 socketio.emit("initial_session_ready")
                 return "phase_1_complete"
        # --- FIN DE CORRECCIÓN ---

        logger.info("🎬 Fase 2: Captura de Datos.")
        if not await _ensure_target_page(page, logger):
             raise DataCaptureError("No se pudo asegurar la página de destino.")

        if not await check_if_logged_in(page):
            _is_first_run_since_startup = True
            raise LoginError("La sesión no está activa a pesar de los chequeos y re-logins.")

        logger.info("Preparando captura concurrente de hora y precios...")
        time_task = asyncio.create_task(capture_market_time(page, logger))
        data_task = asyncio.create_task(capture_premium_data_via_network(page, logger))
        
        await asyncio.sleep(0.5)
        logger.info("Recargando página para disparar APIs...")
        try:
            await page.reload(wait_until="networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            raise LoginError("Timeout en page.reload(). La sesión probablemente expiró y el re-login falló.")
        
        market_time, raw_data = await asyncio.gather(time_task, data_task)

        if not market_time:
            raise DataCaptureError("No se pudo interceptar la hora del mercado.")
        if not raw_data:
            raise DataCaptureError("No se pudo interceptar los datos de precios.")
        if not validate_premium_data(raw_data):
            raise DataCaptureError("Formato de datos no válido.")
        
        logger.info("✓ Hora y datos capturados. Pasando directamente a la base de datos...")
        
        with (app or current_app).app_context():
            store_prices_in_db(raw_data, market_time, app=app)
            
        return "phase_2_complete"

    except Exception as e:
        if isinstance(e, LoginError):
            _is_first_run_since_startup = True
        logger.error(f"Error en la ejecución del bot: {e}", exc_info=True)
        socketio.emit("bot_error", {"message": str(e)})
        with (app or current_app).app_context(): log_error("bot_automation", str(e), traceback.format_exc())
        return f"error: {e}"
    finally:
        _bot_running_lock.release()
        logger.info("=== FIN DE EJECUCIÓN ===")