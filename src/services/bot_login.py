# src/scripts/bot_login.py

from __future__ import annotations
import logging
import random
import asyncio
from typing import Optional

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from .bot_config import (
    LOGIN_URL, ACTIVE_SESSIONS_URL_FRAGMENT,
    CLOSE_ALL_SESSIONS_BUTTON_SELECTOR, HEADER_LOGIN_LINK_SELECTOR,
    LOGIN_PAGE_BUTTON_SELECTOR, USER_INPUT_SELECTOR, PASSWORD_INPUT_SELECTOR,
    SUBMIT_BUTTON_SELECTOR, NAVBAR_TOGGLER_SELECTOR
)
from .bot_page_manager import get_page_manager_instance

logger = logging.getLogger(__name__)

class LoginError(Exception): pass

async def type_like_human(element: Locator, text: str):
    await element.wait_for(state="visible", timeout=15000)
    await asyncio.sleep(random.uniform(0.5, 1.2))
    await element.click()
    await element.fill(text, timeout=10000)
    await asyncio.sleep(random.uniform(0.3, 0.7))

async def click_like_human(locator: Locator): # Parámetro 'page' eliminado
    await locator.wait_for(state="visible", timeout=15000)
    await locator.hover()
    await asyncio.sleep(random.uniform(0.2, 0.6))
    await locator.click()
    await asyncio.sleep(random.uniform(0.5, 1.0))

async def _navigate_to_login_page(page: Page) -> None:
    """Navega desde la página principal hasta el formulario de login."""
    logger.info(f"[Login] Navegando a la página de login: {LOGIN_URL}")
    
    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    if "validate.perfdrive.com" in page.url:
        raise LoginError("Anti-bot detectado en la navegación inicial.")
        
    # Esta sección ya no es necesaria porque navegamos directamente a la página de login
    # y no desde la página principal. Se puede descomentar si se cambia la estrategia.
    # header_login_link = page.locator('#menuppal-login a').first
    # await header_login_link.wait_for(state="visible", timeout=30000) 
    # navbar_toggler = page.locator(NAVBAR_TOGGLER_SELECTOR)
    # if await navbar_toggler.is_visible():
    #     await click_like_human(navbar_toggler)
    # await click_like_human(header_login_link)
    
    # Esperamos y hacemos clic en el botón "Ingresar" del formulario de la página de login
    await page.wait_for_url(f"**{LOGIN_URL}", timeout=25000)
    await click_like_human(page.locator(LOGIN_PAGE_BUTTON_SELECTOR).first)

async def _fill_login_form(page: Page, username: str, password: str) -> None:
    """Rellena y envía el formulario de login."""
    logger.info("[Login] Rellenando credenciales y enviando formulario...")
    username_field = page.locator(USER_INPUT_SELECTOR)
    await username_field.wait_for(state="visible", timeout=20000)
    await type_like_human(username_field, username)
    await type_like_human(page.locator(PASSWORD_INPUT_SELECTOR), password)
    await click_like_human(page.locator(SUBMIT_BUTTON_SELECTOR))

async def _handle_active_sessions(page: Page) -> bool:
    if ACTIVE_SESSIONS_URL_FRAGMENT in page.url:
        logger.warning("[Login] ¡Página de múltiples sesiones detectada! Intentando cerrar todas las sesiones...")
        try:
            close_button = page.locator(CLOSE_ALL_SESSIONS_BUTTON_SELECTOR)
            await close_button.wait_for(state="visible", timeout=10000)
            await click_like_human(close_button)
            await page.wait_for_timeout(3000)
            logger.info("[Login] ✓ Botón 'Cerrar todas las sesiones' presionado.")
            return True
        except PlaywrightError as e:
            logger.error(f"[Login] Error al intentar cerrar sesiones activas: {e}")
            raise LoginError("Fallo al intentar cerrar sesiones activas.")
    return False

async def _try_single_login_attempt(page: Page, username: str, password: str) -> bool:
    """Ejecuta un único intento completo de login. Devuelve True si tiene éxito."""
    await _navigate_to_login_page(page)
    await _fill_login_form(page, username, password)
    await page.wait_for_load_state("domcontentloaded", timeout=45000)
    
    if await _handle_active_sessions(page):
        logger.warning("[Login] Sesiones múltiples cerradas. Se necesita un reintento.")
        return False # Falló, necesita reintentar
    
    return True # Éxito

async def auto_login(page: Optional[Page], username: str, password: str) -> Page:
    """Flujo principal de login con reintentos."""
    if not username or not password:
        raise LoginError("Credenciales no encontradas.")
        
    logger.info("[Login] Iniciando flujo de login con reintentos...")
    page_manager = await get_page_manager_instance()
    
    for attempt in range(1, 4):
        try:
            if not page or page.is_closed():
                page = await page_manager.get_page()
            
            logger.info(f"--- Intento de Login #{attempt} ---")
            if await _try_single_login_attempt(page, username, password):
                logger.info("[Login] ✓ Proceso de login completado con éxito.")
                return page

        except (PlaywrightError, LoginError) as e:
            logger.warning(f"Intento de login #{attempt} falló: {type(e).__name__} - {e}")
            if page and not page.is_closed():
                await page.screenshot(path=f"login_failed_attempt_{attempt}.png")
            page = None # Forzar recreación en el siguiente intento
            if attempt < 3:
                await asyncio.sleep(random.uniform(5.0, 8.0))
            else:
                raise LoginError(f"El login falló después de {attempt} intentos.")

    raise LoginError("El login falló por una razón desconocida.")