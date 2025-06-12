from typing import Tuple, Any, Dict
import json
from playwright.async_api import Page, BrowserContext
from src.config import API_PRIMARY_DATA_PATTERNS

from .config_loader import logger


async def capture_premium_data_via_network(page: Page) -> Tuple[bool, Dict[str, Any], str]:
    """Captura datos premium interceptando las respuestas de la página."""
    logger.info("Capturando datos premium vía red")
    for pattern in API_PRIMARY_DATA_PATTERNS:
        try:
            response = await page.wait_for_response(
                lambda r: r.url.startswith(pattern) and r.status == 200,
                timeout=10000,
            )
            data = json.loads(await response.text())
            return True, data, pattern
        except Exception:
            continue
    return False, {}, ""


async def fetch_premium_data(context: BrowserContext) -> Tuple[bool, Dict[str, Any], str]:
    """Obtiene datos premium desde el contexto cuando no hay respuesta directa."""
    logger.info("Obteniendo datos premium por método alternativo")
    try:
        storage = await context.storage_state()
        return True, storage, "context_state"
    except Exception:
        return False, {}, ""

def validate_premium_data(json_obj: Dict[str, Any]) -> bool:
    """Valida la estructura del JSON de datos premium."""
    return bool(json_obj)


__all__ = [
    "capture_premium_data_via_network",
    "fetch_premium_data",
    "validate_premium_data",
]