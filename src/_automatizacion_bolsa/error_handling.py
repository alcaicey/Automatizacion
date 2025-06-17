from pathlib import Path
from playwright.async_api import Page

from .config_loader import logger, timestamp


async def capture_error_screenshot(page: Page) -> Path:
    """Guarda una captura de pantalla cuando ocurre una excepción."""
    screenshot = Path(f"error_{timestamp}.png")
    try:
        await page.screenshot(path=str(screenshot))
    except Exception as exc:
        logger.error(f"No se pudo guardar screenshot: {exc}")
    return screenshot


__all__ = ["capture_error_screenshot"]