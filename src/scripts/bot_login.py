# src/scripts/bot_login.py

from __future__ import annotations
import logging
import random
import asyncio
from typing import Final

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from src.config import ACTIVE_SESSIONS_URL_FRAGMENT, CLOSE_ALL_SESSIONS_BUTTON_SELECTOR
from .bot_page_manager import recreate_page

logger = logging.getLogger(__name__)

class LoginError(Exception):
    pass

BASE_URL: Final[str] = "https://www.bolsadesantiago.com"
LOGIN_LANDING_PAGE_URL: Final[str] = f"{BASE_URL}/login"
TARGET_DATA_PAGE_URL: Final[str] = f"{BASE_URL}/plus_acciones_precios"
SSO_URL_FRAGMENT: Final[str] = "sso.bolsadesantiago.com"

HEADER_LOGIN_LINK_SELECTOR = '#menuppal-login a'
LOGIN_PAGE_BUTTON_SELECTOR = 'button.btn:has-text("Ingresar")'
USER_SEL = "#username"
PASS_SEL = "#password"
NAVBAR_TOGGLER_SELECTOR = 'button.navbar-toggler'

async def type_like_human(element: Locator, text: str):
    await element.wait_for(state="visible", timeout=15000)
    await asyncio.sleep(random.uniform(0.5, 1.2))
    await element.click()
    await element.fill(text, timeout=10000)
    await asyncio.sleep(random.uniform(0.3, 0.7))

async def click_like_human(page: Page, locator: Locator):
    await locator.wait_for(state="visible", timeout=15000)
    await locator.hover()
    await asyncio.sleep(random.uniform(0.2, 0.6))
    await locator.click()
    await asyncio.sleep(random.uniform(0.5, 1.0))

async def _handle_active_sessions(page: Page) -> bool:
    if ACTIVE_SESSIONS_URL_FRAGMENT in page.url:
        logger.warning("[Login] ¡Página de múltiples sesiones detectada! Intentando cerrar todas las sesiones...")
        try:
            close_button = page.locator(CLOSE_ALL_SESSIONS_BUTTON_SELECTOR)
            await close_button.wait_for(state="visible", timeout=10000)
            await click_like_human(page, close_button)
            await page.wait_for_timeout(3000)
            logger.info("[Login] ✓ Botón 'Cerrar todas las sesiones' presionado.")
            return True
        except Exception as e:
            logger.error(f"[Login] Error al intentar cerrar sesiones activas: {e}")
            raise LoginError("Fallo al intentar cerrar sesiones activas.")
    return False

async def auto_login(page: Page, username: str, password: str) -> Page:
    if not username or not password:
        raise LoginError("Credenciales no encontradas en el entorno.")
        
    logger.info("[Login] Iniciando flujo de login progresivo y evasivo...")
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            if not page or page.is_closed():
                logger.warning(f"[Login] La página fue cerrada. Recreando para el intento #{attempt}...")
                page = await recreate_page()

            logger.info(f"[Login] Intento de login #{attempt}: Navegando a la página principal.")
            
            await page.goto(BASE_URL, wait_until="networkidle", timeout=45000)
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # VERIFICACIÓN ANTI-BOT PROACTIVA
            if "validate.perfdrive.com" in page.url:
                logger.warning(f"[Login] ¡Anti-bot detectado en el intento #{attempt}! Esperando para reintentar...")
                await asyncio.sleep(random.uniform(10.0, 15.0))
                continue # Salta al siguiente intento del bucle

            logger.info("[Login] Esperando a que el enlace de login esté visible...")
            header_login_link = page.locator(HEADER_LOGIN_LINK_SELECTOR).first
            await header_login_link.wait_for(state="visible", timeout=25000)
            
            navbar_toggler = page.locator(NAVBAR_TOGGLER_SELECTOR)
            if await navbar_toggler.is_visible():
                await click_like_human(page, navbar_toggler)
            
            await click_like_human(page, header_login_link)
            await page.wait_for_url(f"**{LOGIN_LANDING_PAGE_URL}", timeout=25000)

            login_page_button = page.locator(LOGIN_PAGE_BUTTON_SELECTOR).first
            await click_like_human(page, login_page_button)
            
            username_field = page.locator(USER_SEL)
            await username_field.wait_for(state="visible", timeout=20000)
            
            logger.info("[Login] Rellenando credenciales...")
            await type_like_human(username_field, username)
            await type_like_human(page.locator(PASS_SEL), password)
            
            logger.info("[Login] Enviando formulario...")
            submit_button = page.locator("input[type='submit']")
            await click_like_human(page, submit_button)
            
            await page.wait_for_load_state("domcontentloaded", timeout=45000)
            await asyncio.sleep(random.uniform(2.5, 4.0))

            if await _handle_active_sessions(page):
                logger.warning("[Login] Sesiones múltiples cerradas. Reiniciando el flujo de login.")
                continue 
            
            logger.info("[Login] ✓ Proceso de login completado con éxito.")
            return page

        except PlaywrightTimeoutError as e:
            if attempt < max_attempts:
                logger.warning(f"[Login] Timeout en intento #{attempt} ({e}). Reintentando...")
                await page.screenshot(path=f"login_timeout_attempt_{attempt}.png")
                await asyncio.sleep(random.uniform(5.0, 8.0))
                continue
            else:
                logger.error(f"[Login] Timeout final en intento #{attempt}. Fallo crítico.")
                raise LoginError(f"Error de Timeout no recuperable tras {attempt} intentos: {e}")

        except PlaywrightError as e:
            if "Target page, context or browser has been closed" in str(e):
                logger.error(f"[Login] El anti-bot cerró la página durante el intento #{attempt}. Se reintentará.")
                page = None # Forzar la recreación de la página
                if attempt < max_attempts:
                    await asyncio.sleep(random.uniform(7.0, 10.0))
                    continue
            
            if attempt == max_attempts:
                raise LoginError(f"Error de Playwright no recuperable tras {attempt} intentos: {e}")
            else:
                logger.warning(f"Error de Playwright en el intento #{attempt}: {e}. Reintentando...")

        except Exception as e:
            if attempt == max_attempts:
                logger.error(f"[Login] Fallo crítico final: {e}", exc_info=True)
                raise LoginError(f"No se pudo completar el auto-login tras {max_attempts} intentos: {e}")
            else:
                 logger.warning(f"Intento de login #{attempt} falló con error general: {e}. Reintentando...")

    raise LoginError(f"El flujo de login falló después de {max_attempts} intentos.")