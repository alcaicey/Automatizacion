import json
import logging
from typing import Tuple, Any, Dict, Optional
from datetime import datetime
from playwright.async_api import Page, Response, TimeoutError as PlaywrightTimeoutError
from src.config import API_PRIMARY_DATA_PATTERNS

class DataCaptureError(Exception): pass

MARKET_TIME_URL_FRAGMENT = "api/Comunes/getHoraMercado"
SESSION_STATUS_URL_FRAGMENT = "api/Comunes/getEstadoSesionUsuario"

async def capture_market_time(page: Page, logger_instance=None) -> Optional[datetime]:
    log = logger_instance or logging.getLogger(__name__)
    log.info("[DataCapture] 🕒 Escuchando por la hora del mercado...")
    def is_time_response(response: Response) -> bool:
        return response.status == 200 and MARKET_TIME_URL_FRAGMENT in response.url
    try:
        async with page.expect_response(is_time_response, timeout=15000) as response_info:
            response = await response_info.value
        data = await response.json()
        hora_str = data.get("HORA")
        if not hora_str: raise DataCaptureError("API de hora no contiene 'HORA'.")
        try: market_time = datetime.strptime(hora_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError: market_time = datetime.strptime(hora_str, "%Y-%m-%d %H:%M:%S")
        log.info(f"[DataCapture] ✓ Hora del mercado interceptada: {market_time}")
        return market_time
    except Exception as e:
        log.error(f"[DataCapture] Fallo al capturar la hora del mercado: {e}")
        return None

async def capture_premium_data_via_network(page: Page, logger_instance=None) -> Optional[Dict[str, Any]]:
    log = logger_instance or logging.getLogger(__name__)
    log.info("[DataCapture] 📡 Escuchando por los datos de precios...")
    def is_target_response(response: Response) -> bool:
        return response.status == 200 and any(p in response.url for p in API_PRIMARY_DATA_PATTERNS)
    try:
        async with page.expect_response(is_target_response, timeout=30000) as response_info:
            response = await response_info.value
        log.info(f"[DataCapture] ✓ ¡Precios capturados! URL: {response.url}")
        return await response.json()
    except Exception as e:
        log.error(f"[DataCapture] Fallo al capturar precios: {e}")
        return None

async def capture_session_time_via_network(page: Page, logger_instance=None) -> Optional[int]:
    """Escucha la respuesta de la API de estado de sesión y extrae el tiempo restante."""
    log = logger_instance or logging.getLogger(__name__)
    log.info("[DataCapture] ⏳ Escuchando por el estado de la sesión post-login...")
    
    def is_session_response(response: Response) -> bool:
        return response.status == 200 and SESSION_STATUS_URL_FRAGMENT in response.url
        
    try:
        # Esperamos un tiempo razonable para que la API sea llamada tras el login.
        async with page.expect_response(is_session_response, timeout=20000) as response_info:
            response = await response_info.value
        data = await response.json()
        remaining_time = data.get("tiempoRestante")
        if remaining_time is not None:
            log.info(f"[DataCapture] ✓ ¡Variable de sesión encontrada! Duración: {remaining_time} segundos (~{int(remaining_time)/60:.1f} minutos).")
            return int(remaining_time)
        return None
    except Exception as e:
        log.warning(f"[DataCapture] No se interceptó la API de sesión post-login. Se usará duración por defecto. Error: {type(e).__name__}")
        return None

def validate_premium_data(json_obj: Any) -> bool:
    if isinstance(json_obj, dict) and "listaResult" in json_obj: return True
    if isinstance(json_obj, list): return True
    return False