from playwright.sync_api import sync_playwright

from .config_loader import logger
from src.config import INITIAL_PAGE_URL

_p_instance = None
_browser = None
_context = None
_page = None


def create_page(sync_pw=sync_playwright):
    """Inicia Playwright y devuelve una nueva página."""
    global _p_instance, _browser, _context, _page
    _p_instance = sync_pw().start()
    _browser = _p_instance.chromium.launch()
    _context = _browser.new_context()
    _page = _context.new_page()
    _page.goto(INITIAL_PAGE_URL)
    return _page


def get_active_page():
    return _page


def close_resources():
    """Cierra de forma segura recursos de Playwright."""
    try:
        if _context:
            _context.close()
        if _browser:
            _browser.close()
        if _p_instance:
            _p_instance.stop()
    except Exception as exc:
        logger.error(f"Error cerrando Playwright: {exc}")


__all__ = ["create_page", "get_active_page", "close_resources"]
