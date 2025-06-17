import json
import logging
from typing import Optional, Tuple, Any, Dict
from playwright.async_api import Page, Response, TimeoutError as PlaywrightTimeoutError
from src.config import API_PRIMARY_DATA_PATTERNS

# --- INICIO DE LA CORRECCIÓN ---
# Definir la excepción personalizada en este módulo
class DataCaptureError(Exception):
    """Excepción para errores durante el proceso de captura de datos de la red."""
    pass
# --- FIN DE LA CORRECCIÓN ---

async def capture_premium_data_via_network(page: Page, logger_instance=None) -> Tuple[bool, Dict[str, Any], str]:
    log = logger_instance or logging.getLogger(__name__)
    log.info("[DataCapture] 📡 Captura de datos por red iniciada...")

    def is_target_response(response: Response) -> bool:
        return response.status == 200 and any(pattern in response.url for pattern in API_PRIMARY_DATA_PATTERNS)

    try:
        log.info(f"[DataCapture] Escuchando peticiones que coincidan con: {API_PRIMARY_DATA_PATTERNS}")
        
        async with page.expect_response(is_target_response, timeout=30000) as response_info:
            response = await response_info.value
        
        log.info(f"[DataCapture] ✓ ¡RESPUESTA CAPTURADA! URL: {response.url}")
        data = await response.json()
        
        matched_pattern = next((p for p in API_PRIMARY_DATA_PATTERNS if p in response.url), "")
        
        return True, data, matched_pattern

    except PlaywrightTimeoutError:
        log.error("[DataCapture] Timeout. No se recibió ninguna respuesta de red válida.")
        return False, {}, ""
    except Exception as e:
        log.error(f"[DataCapture] Error inesperado durante la captura de red: {e}", exc_info=True)
        return False, {}, ""

def validate_premium_data(json_obj: Any) -> bool:
    """Valida la estructura del JSON de datos premium."""
    if isinstance(json_obj, dict) and "listaResult" in json_obj and isinstance(json_obj["listaResult"], list):
        return True
    if isinstance(json_obj, list): # Aceptar también listas directamente
        return True
    return False

# Asegurarse de exportar la nueva excepción
__all__ = [
    "capture_premium_data_via_network",
    "validate_premium_data",
    "DataCaptureError",
]