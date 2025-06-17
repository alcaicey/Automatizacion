from __future__ import annotations
import logging
import os
import random
import asyncio
from typing import Final

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class LoginError(Exception):
    pass

TARGET_DATA_PAGE_URL: Final[str] = "https://www.bolsadesantiago.com/plus_acciones_precios"
LOGIN_PAGE_URL_FRAGMENT = "sso.bolsadesantiago.com"
LOGIN_IFRAME_SELECTOR = f"iframe[src*='{LOGIN_PAGE_URL_FRAGMENT}']"
USER_SEL = "#username"
PASS_SEL = "#password"

async def type_like_human(element: Locator, text: str):
    """Escribe en un campo letra por letra con un retraso aleatorio."""
    await element.wait_for(state="visible", timeout=15000)
    for char in text:
        await element.press(char)
        await asyncio.sleep(random.uniform(0.08, 0.25))

async def auto_login(page: Page, username: str, password: str) -> bool:
    """
    Realiza el proceso de login automático, usando las credenciales proporcionadas.
    """
    if not username or not password:
        logger.error("[Login] [Paso 3.1] Credenciales vacías recibidas.")
        raise LoginError("Credenciales no encontradas en el entorno.")
        
    logger.info("[Login] [Paso 3.2] Buscando el formulario de inicio de sesión...")
    
    try:
        search_context: Page | Locator = page
        
        if LOGIN_PAGE_URL_FRAGMENT in page.url:
            logger.info("[Login] [Paso 3.3.A] Redirección a página de login detectada.")
        else:
            logger.info("[Login] [Paso 3.3.B] Buscando iframe de login...")
            iframe_locator = page.locator(LOGIN_IFRAME_SELECTOR)
            try:
                await iframe_locator.wait_for(state="visible", timeout=5000)
                search_context = page.frame_locator(LOGIN_IFRAME_SELECTOR)
            except PlaywrightTimeoutError:
                logger.warning("[Login] [Paso 3.3.D] No se encontró iframe. Asumiendo sesión activa.")
                return True

        logger.info("[Login] [Paso 3.4] Rellenando credenciales...")
        await type_like_human(search_context.locator(USER_SEL), username)
        await type_like_human(search_context.locator(PASS_SEL), password)
        
        logger.info("[Login] [Paso 3.5] Enviando formulario...")
        await search_context.locator("input[type='submit']").click()
        return True
        
    except Exception as e:
        logger.error(f"[Login] Fallo crítico durante el proceso de login: {e}", exc_info=True)
        try:
            await page.screenshot(path="error_login_failed.png")
        except Exception as se:
            logger.error(f"No se pudo guardar la captura de pantalla del error: {se}")
        raise LoginError(f"No se pudo completar el auto-login: {e}")