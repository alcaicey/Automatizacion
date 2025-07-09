# src/utils/page_utils.py

from playwright.async_api import Page
from src.config import TARGET_DATA_PAGE_URL
import logging

logger_default = logging.getLogger(__name__)

async def _ensure_target_page(page: Page, logger=None) -> bool:
    """Asegura que el navegador esté en la URL de destino y recarga si es necesario."""
    logger = logger or logger_default  # Usa el logger entregado o el default

    try:
        if TARGET_DATA_PAGE_URL not in page.url:
            logger.warning("La URL actual no es la esperada. Redirigiendo...")
            await page.goto(TARGET_DATA_PAGE_URL)
            await page.wait_for_load_state("load")
        return True
    except Exception as e:
        logger.exception("Error asegurando la página de destino: %s", e)
        return False
