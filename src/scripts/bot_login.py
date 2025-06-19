from __future__ import annotations
import logging
import os
import random
import asyncio
from typing import Final, Tuple

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
# Ya no es necesario importar esto aquí
# from .bot_data_capture import capture_session_time_via_network

logger = logging.getLogger(__name__)

class LoginError(Exception):
    pass

TARGET_DATA_PAGE_URL: Final[str] = "https://www.bolsadesantiago.com/plus_acciones_precios"
LOGIN_PAGE_URL_FRAGMENT = "sso.bolsadesantiago.com"
LOGIN_IFRAME_SELECTOR = f"iframe[src*='{LOGIN_PAGE_URL_FRAGMENT}']"
USER_SEL = "#username"
PASS_SEL = "#password"

async def type_like_human(element: Locator, text: str):
    await element.wait_for(state="visible", timeout=15000)
    for char in text:
        await element.press(char)
        await asyncio.sleep(random.uniform(0.08, 0.25))

async def auto_login(page: Page, username: str, password: str) -> None:
    """
    Realiza el proceso de login y espera a que la navegación a la página de destino termine.
    Lanza una excepción LoginError si falla.
    """
    if not username or not password:
        logger.error("[Login] Credenciales vacías recibidas.")
        raise LoginError("Credenciales no encontradas en el entorno.")
        
    logger.info("[Login] Buscando el formulario de inicio de sesión...")
    
    try:
        search_context: Page | Locator = page
        
        if LOGIN_PAGE_URL_FRAGMENT not in page.url:
            logger.info("[Login] Buscando iframe de login...")
            iframe_locator = page.locator(LOGIN_IFRAME_SELECTOR)
            try:
                await iframe_locator.wait_for(state="visible", timeout=10000)
                search_context = page.frame_locator(LOGIN_IFRAME_SELECTOR)
                logger.info("[Login] Iframe de login encontrado.")
            except PlaywrightTimeoutError:
                # Si no hay iframe, puede que ya estemos logueados. El llamador se encargará.
                logger.warning("[Login] No se encontró iframe. Se asume que no es necesaria una acción de login aquí.")
                return

        logger.info("[Login] Rellenando credenciales...")
        await type_like_human(search_context.locator(USER_SEL), username)
        await type_like_human(search_context.locator(PASS_SEL), password)
        
        logger.info("[Login] Enviando formulario y esperando redirección...")
        # Hacemos click y esperamos explícitamente a que la URL cambie a la página de destino.
        # Esto es mucho más robusto que esperar un tiempo fijo.
        async with page.expect_navigation(url=f"**{TARGET_DATA_PAGE_URL}**", timeout=45000):
            await search_context.locator("input[type='submit']").click()
        
        logger.info("[Login] ✓ Redirección a la página de datos completada.")
        
    except Exception as e:
        logger.error(f"[Login] Fallo crítico durante el proceso de auto-login: {e}", exc_info=True)
        try:
            await page.screenshot(path="error_login_failed.png")
        except Exception as se:
            logger.error(f"No se pudo guardar la captura de pantalla del error: {se}")
        raise LoginError(f"No se pudo completar el auto-login: {e}")