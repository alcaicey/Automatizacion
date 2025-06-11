from playwright.async_api import (
    Playwright,
    Browser,
    BrowserContext,
)

from .config_loader import logger
from src.config import INITIAL_PAGE_URL

_browser: Browser | None = None
_context: BrowserContext | None = None
_page = None


async def create_page(pw: Playwright) -> None:
    """Inicia Playwright y devuelve una nueva página."""
    global _browser, _context, _page
    _browser = await pw.chromium.launch()
    _context = await _browser.new_context()
    _page = await _context.new_page()
    await _page.goto(INITIAL_PAGE_URL)
    return _page


def get_active_page():
    return _page


async def close_resources() -> None:
    """Cierra de forma segura recursos de Playwright."""
    try:
        if _context:
            await _context.close()
        if _browser:
            await _browser.close()
    except Exception as exc:
        logger.error(f"Error cerrando Playwright: {exc}")


__all__ = ["create_page", "get_active_page", "close_resources"]
