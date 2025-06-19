from __future__ import annotations
import asyncio
import logging
import traceback
from flask import current_app
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .bot_page_manager import get_page
from .bot_login import auto_login, LoginError, TARGET_DATA_PAGE_URL
from .bot_data_capture import capture_market_time, capture_premium_data_via_network, validate_premium_data, DataCaptureError
from src.utils.db_io import store_prices_in_db
from src.extensions import socketio
from src.routes.errors import log_error
# --- INICIO DE CORRECCIÓN: Importar el nuevo helper ---
from src.utils.page_utils import _ensure_target_page
# --- FIN DE CORRECCIÓN ---

logger = logging.getLogger(__name__)
_bot_running_lock = asyncio.Lock()
_is_first_run_since_startup = True

async def check_if_logged_in(page: Page) -> bool:
    logger.info("[Service] Verificando si existe una sesión activa...")
    try:
        await page.locator("span.badge:has-text('Tiempo Real')").first.wait_for(state="visible", timeout=15000)
        logger.info("[Service] ✓ Sesión activa encontrada (indicador 'Tiempo Real').")
        return True
    except PlaywrightTimeoutError:
        logger.warning("[Service] No se encontró indicador de sesión activa.")
        return False

async def run_bolsa_bot(app=None, username=None, password=None, **kwargs) -> str | None:
    global _is_first_run_since_startup

    try:
        await asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)
        lock_acquired = True
    except asyncio.TimeoutError:
        lock_acquired = False

    if not lock_acquired:
        return "ignored_already_running"
    
    try:
        logger.info(f"=== INICIO DE EJECUCIÓN (Primera vez: {_is_first_run_since_startup}) ===")
        page = await get_page()

        # --- INICIO DE CORRECCIÓN: Eliminar page.goto() y usar el helper ---
        # Ya no navegamos aquí. La navegación se maneja de forma más inteligente.
        # await page.goto(TARGET_DATA_PAGE_URL, wait_until="networkidle") 
        # --- FIN DE CORRECCIÓN ---

        if _is_first_run_since_startup:
            logger.info("🚀 Fase 1: Establecimiento de Sesión.")
            # --- INICIO DE CORRECCIÓN: La navegación inicial se hace aquí ---
            await page.goto(TARGET_DATA_PAGE_URL, wait_until="networkidle")
            # --- FIN DE CORRECCIÓN ---
            if not await check_if_logged_in(page):
                logger.info("Sesión no activa. Intentando auto-login...")
                await auto_login(page, username, password)
                await page.wait_for_url(f"**{TARGET_DATA_PAGE_URL}**", timeout=45000)
                if not await check_if_logged_in(page):
                    raise LoginError("Login fallido.")
            _is_first_run_since_startup = False
            socketio.emit("initial_session_ready")
            return "phase_1_complete"

        logger.info("🎬 Fase 2: Captura de Datos.")

        # --- INICIO DE CORRECCIÓN: Asegurar que estamos en la página correcta ---
        if not await _ensure_target_page(page, logger):
             raise DataCaptureError("No se pudo asegurar la página de destino.")
        # --- FIN DE CORRECCIÓN ---

        if not await check_if_logged_in(page):
            _is_first_run_since_startup = True
            raise LoginError("La sesión ha expirado.")

        logger.info("Preparando captura concurrente de hora y precios...")
        time_task = asyncio.create_task(capture_market_time(page, logger))
        data_task = asyncio.create_task(capture_premium_data_via_network(page, logger))
        
        await asyncio.sleep(1)
        logger.info("Recargando página para disparar APIs...")
        await page.reload(wait_until="networkidle")
        
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
        logger.error(f"Error en la ejecución del bot: {e}", exc_info=True)
        socketio.emit("bot_error", {"message": str(e)})
        with (app or current_app).app_context(): log_error("bot_automation", str(e), traceback.format_exc())
        return f"error: {e}"
    finally:
        _bot_running_lock.release()
        logger.info("=== FIN DE EJECUCIÓN ===")