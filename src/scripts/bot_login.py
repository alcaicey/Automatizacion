from __future__ import annotations
import logging
import os
import random
import asyncio
from typing import Final, Tuple

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from .bot_data_capture import capture_session_time_via_network

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

async def auto_login(page: Page, username: str, password: str) -> Tuple[bool, int | None]:
    """
    Realiza el proceso de login y captura el tiempo de sesión inicial.
    Devuelve (True, session_duration_seconds) o (False, None).
    """
    if not username or not password:
        logger.error("[Login] Credenciales vacías recibidas.")
        raise LoginError("Credenciales no encontradas en el entorno.")
        
    logger.info("[Login] Buscando el formulario de inicio de sesión...")
    
    try:
        search_context: Page | Locator = page
        
        if LOGIN_PAGE_URL_FRAGMENT in page.url:
            logger.info("[Login] Redirección a página de login detectada.")
        else:
            logger.info("[Login] Buscando iframe de login...")
            iframe_locator = page.locator(LOGIN_IFRAME_SELECTOR)
            try:
                await iframe_locator.wait_for(state="visible", timeout=5000)
                search_context = page.frame_locator(LOGIN_IFRAME_SELECTOR)
            except PlaywrightTimeoutError:
                logger.warning("[Login] No se encontró iframe. Asumiendo sesión activa.")
                return True, None # No hay login, no podemos capturar nuevo tiempo.

        logger.info("[Login] Rellenando credenciales...")
        await type_like_human(search_context.locator(USER_SEL), username)
        await type_like_human(search_context.locator(PASS_SEL), password)
        
        logger.info("[Login] Enviando formulario y escuchando APIs post-login...")

        # Creamos dos tareas que correrán en paralelo:
        # 1. La escucha de la API de sesión.
        # 2. El click en el botón de login.
        session_time_task = asyncio.create_task(capture_session_time_via_network(page, logger))
        
        # Le damos un respiro para que el listener se active
        await asyncio.sleep(0.5)

        # Hacemos click y no esperamos, dejando que la tarea de escucha capture la respuesta durante la redirección.
        await search_context.locator("input[type='submit']").click()
        
        # Esperamos a que la tarea de captura de tiempo termine.
        session_duration = await session_time_task

        return True, session_duration
        
    except Exception as e:
        logger.error(f"[Login] Fallo crítico durante el proceso de login: {e}", exc_info=True)
        try:
            await page.screenshot(path="error_login_failed.png")
        except Exception as se:
            logger.error(f"No se pudo guardar la captura de pantalla del error: {se}")
        raise LoginError(f"No se pudo completar el auto-login: {e}")