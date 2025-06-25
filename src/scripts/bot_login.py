from __future__ import annotations
import logging
import random
import asyncio
from typing import Final

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class LoginError(Exception):
    pass

# Constantes
BASE_URL: Final[str] = "https://www.bolsadesantiago.com"
LOGIN_LANDING_PAGE_URL: Final[str] = f"{BASE_URL}/login"
TARGET_DATA_PAGE_URL: Final[str] = f"{BASE_URL}/plus_acciones_precios"
SSO_URL_FRAGMENT: Final[str] = "sso.bolsadesantiago.com"

# Selectores
HEADER_LOGIN_LINK_SELECTOR = '#menuppal-login a'
LOGIN_PAGE_BUTTON_SELECTOR = 'button.btn:has-text("Ingresar")'
USER_SEL = "#username"
PASS_SEL = "#password"
NAVBAR_TOGGLER_SELECTOR = 'button.navbar-toggler'

async def type_like_human(element: Locator, text: str):
    await element.wait_for(state="visible", timeout=15000)
    await element.fill(text)

async def auto_login(page: Page, username: str, password: str) -> None:
    if not username or not password:
        logger.error("[Login] Credenciales vacías recibidas.")
        raise LoginError("Credenciales no encontradas en el entorno.")
        
    logger.info("[Login] Iniciando flujo de login progresivo...")
    
    try:
        # PASOS 1 y 2: Navegar a la home y manejar menú responsivo
        if BASE_URL not in page.url:
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        
        navbar_toggler = page.locator(NAVBAR_TOGGLER_SELECTOR)
        if await navbar_toggler.is_visible():
            await navbar_toggler.click()
            await page.wait_for_timeout(500)
        
        # PASO 3: Clic en "Ingresar a Mi Perfil"
        header_login_link = page.locator(HEADER_LOGIN_LINK_SELECTOR).first
        await header_login_link.click()
        await page.wait_for_url(f"**{LOGIN_LANDING_PAGE_URL}", timeout=20000)
        logger.info(f"[Login] En la página {page.url}")

        # PASO 4: Clic en el botón "INGRESAR" y esperar a que el formulario de SSO esté listo
        login_page_button = page.locator(LOGIN_PAGE_BUTTON_SELECTOR).first
        await login_page_button.click()
        
        # En lugar de esperar por la URL, esperamos directamente por el campo de email en la página de SSO.
        # Esto es mucho más fiable.
        logger.info("[Login] Esperando a que el formulario de SSO sea visible...")
        username_field = page.locator(USER_SEL)
        await username_field.wait_for(state="visible", timeout=20000)
        logger.info("[Login] Formulario de SSO detectado.")

        # PASO 5: Rellenar credenciales en la página de SSO
        logger.info("[Login] Rellenando credenciales...")
        await type_like_human(page.locator(USER_SEL), username)
        await type_like_human(page.locator(PASS_SEL), password)
        
        # PASO 6: Enviar y esperar redirección final
        logger.info("[Login] Enviando formulario y esperando redirección final...")
        await page.locator("input[type='submit']").click()
        await page.wait_for_load_state("networkidle", timeout=45000)

        logger.info("[Login] ✓ Proceso de login completado.")
        
    except Exception as e:
        logger.error(f"[Login] Fallo crítico durante el proceso de auto-login: {e}", exc_info=True)
        try:
            screenshot_path = "error_login_failed.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"Captura de pantalla del error guardada en: {screenshot_path}")
        except Exception as se:
            logger.error(f"No se pudo guardar la captura de pantalla del error: {se}")
        raise LoginError(f"No se pudo completar el auto-login: {e}")