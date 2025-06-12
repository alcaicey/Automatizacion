
from __future__ import annotations
import asyncio, os, logging, random
from typing import Final
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

USERNAME: Final[str] = os.getenv("BOLSA_USERNAME", "")
PASSWORD: Final[str] = os.getenv("BOLSA_PASSWORD", "")

LOGIN_IFRAME = "iframe[src*='autenticacion']"
USERNAME_SELECTOR = "#username, input[name='rut']"
PASSWORD_SELECTOR = "#password, input[name='password']"
LOGIN_BTN_SELECTOR = "#login-button, button[type='submit']"

TARGET_DATA_PAGE_URL = os.getenv("TARGET_DATA_PAGE_URL", "https://www.bolsadesantiago.com/plus_acciones_precios")

async def _type_slow(page: Page, selector: str, text: str):
    """Escribe carácter por carácter con retraso aleatorio."""
    for ch in text:
        await page.type(selector, ch, delay=random.randint(60, 140))
    await asyncio.sleep(random.uniform(0.2, 0.6))

async def perform_login(page: Page) -> None:
    if page.url.startswith(TARGET_DATA_PAGE_URL):
        return

    frame = page
    try:
        loc = page.locator(LOGIN_IFRAME)
        if await loc.is_visible(timeout=5_000):
            frame = await (await loc.first).content_frame()  # type: ignore[arg-type]
    except PlaywrightTimeoutError:
        pass

    # Intenta escribir usuario lentamente; si selector no existe se asume sesión
    try:
        await frame.wait_for_selector(USERNAME_SELECTOR, timeout=7_000)
    except PlaywrightTimeoutError:
        logger.info("Campos de login no visibles; asumiendo sesión iniciada.")
        return

    await _type_slow(frame, USERNAME_SELECTOR, USERNAME)
    await _type_slow(frame, PASSWORD_SELECTOR, PASSWORD)
    await frame.click(LOGIN_BTN_SELECTOR, timeout=20_000)
    await page.wait_for_url("**/plus_**", timeout=60_000)
