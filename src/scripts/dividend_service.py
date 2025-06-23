# src/scripts/dividend_service.py

import logging
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.extensions import db, socketio
from src.models import Dividend
from src.utils.page_utils import _ensure_target_page

logger = logging.getLogger(__name__)

DIVIDEND_PAGE_URL = "https://www.bolsadesantiago.com/dividendos"
DIVIDEND_API_PATTERN = "api/RV_ResumenMercado/getDividendos"

# Definición de la excepción personalizada
class DataCaptureError(Exception): pass

async def fetch_dividends_with_playwright(page: Page) -> List[Dict[str, Any]] | None:
    """Navega a la página de dividendos e intercepta la respuesta de la API."""
    logger.info("[DividendService] Navegando a la página de dividendos para interceptar datos...")
    
    if DIVIDEND_PAGE_URL not in page.url:
         await page.goto(DIVIDEND_PAGE_URL, wait_until="domcontentloaded", timeout=30000)

    try:
        # Iniciar el listener ANTES de la acción que dispara la red.
        async with page.expect_response(lambda r: DIVIDEND_API_PATTERN in r.url, timeout=25000) as response_info:
            logger.info("[DividendService] Listener de red activo. Recargando la página para forzar la petición...")
            await page.reload(wait_until="domcontentloaded", timeout=25000)
        
        response = await response_info.value
        if response.status != 200:
            logger.error(f"API de dividendos respondió con status {response.status}")
            raise DataCaptureError(f"La API de dividendos respondió con un error: status {response.status}")
            
        data = await response.json()
        if "listaResult" in data and isinstance(data["listaResult"], list):
            logger.info(f"✓ API de dividendos interceptada con {len(data['listaResult'])} registros.")
            return data["listaResult"]
        
        logger.warning("Respuesta de API de dividendos no tiene el formato esperado.")
        raise DataCaptureError("El formato de la respuesta de la API de dividendos no es el esperado.")

    except PlaywrightTimeoutError:
        error_msg = "Timeout esperando la respuesta de la API de dividendos. La página podría no haberla cargado o la red es lenta."
        logger.error(error_msg)
        raise DataCaptureError(error_msg) from None
    except Exception as e:
        logger.error(f"Error inesperado al capturar dividendos con Playwright: {e}", exc_info=True)
        raise DataCaptureError(f"Error inesperado durante la captura: {e}") from e

def _process_api_item(item: Dict[str, Any]) -> Dict[str, Any] | None:
    """Convierte un item de la API a un formato limpio y validado para la DB."""
    try:
        def safe_float(key):
            value = item.get(key)
            return float(value) if value is not None else None
        
        def safe_int(key):
             value = item.get(key)
             return int(value) if value is not None else None

        return {
            "nemo": item.get("nemo"),
            "description": item.get("descrip_vc"),
            "limit_date": datetime.strptime(item["fec_lim"], "%Y-%m-%d").date(),
            "payment_date": datetime.strptime(item["fec_pago"], "%Y-%m-%d").date(),
            "currency": item.get("moneda"),
            "value": safe_float("val_acc"),
            "num_acc_ant": safe_int("num_acc_ant"),
            "num_acc_der": safe_int("num_acc_der"),
            "num_acc_nue": safe_int("num_acc_nue"),
            "pre_ant_vc": safe_float("pre_ant_vc"),
            "pre_ex_vc": safe_float("pre_ex_vc"),
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Omitiendo registro de dividendo mal formado: {item}. Error: {e}")
        return None

async def compare_and_update_dividends(page: Page) -> Dict[str, Any]:
    """Compara los dividendos de la API con la DB, informa los cambios y actualiza."""
    # La excepción de fetch_dividends_with_playwright se propagará hacia arriba si ocurre
    new_data_raw = await fetch_dividends_with_playwright(page)

    new_dividends_processed = [d for d in (_process_api_item(item) for item in new_data_raw) if d]
    old_dividends = Dividend.query.all()

    # --- INICIO DE LA CORRECCIÓN DE SERIALIZACIÓN ---

    # Creamos un mapa de los objetos SQLAlchemy de la DB para poder acceder a su método .to_dict()
    old_map_objects = {(d.nemo, d.payment_date, d.description): d for d in old_dividends}
    old_keys = set(old_map_objects.keys())
    
    # El mapa de los nuevos datos contiene objetos `date` de Python, que no son serializables.
    # Necesitamos convertirlos a strings.
    new_map = {(d['nemo'], d['payment_date'], d['description']): d for d in new_dividends_processed}
    new_keys = set(new_map.keys())

    # Funciones para convertir diccionarios con objetos `date` a diccionarios con strings.
    def serialize_dividend_dict(d):
        d_copy = d.copy()
        if isinstance(d_copy.get('payment_date'), date):
            d_copy['payment_date'] = d_copy['payment_date'].isoformat()
        if isinstance(d_copy.get('limit_date'), date):
            d_copy['limit_date'] = d_copy['limit_date'].isoformat()
        return d_copy

    # Encontrar diferencias
    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys
    
    changes = {
        # Convertimos los diccionarios de la lista 'added' para que sean serializables
        "added": [serialize_dividend_dict(new_map[key]) for key in added_keys],
        # 'removed' se convierte usando el método .to_dict() del objeto del modelo, que ya serializa.
        "removed": [old_map_objects[key].to_dict() for key in removed_keys],
    }
    
    # --- FIN DE LA CORRECCIÓN DE SERIALIZACIÓN ---
    
    has_changes = any(changes.values())
    if has_changes:
        logger.info("Cambios detectados en dividendos. Actualizando base de datos.")
        try:
            Dividend.query.delete()
            db.session.flush()
            # Usamos los datos procesados (con objetos `date`) para crear las nuevas entradas en la DB
            new_db_entries = [Dividend(**data) for data in new_dividends_processed]
            db.session.add_all(new_db_entries)
            db.session.commit()
            logger.info(f"✓ Base de datos de dividendos actualizada con {len(new_db_entries)} registros.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar la tabla de dividendos: {e}", exc_info=True)
            return {"error": f"Error de base de datos durante la actualización: {str(e)}"}

    return {
        "has_changes": has_changes,
        "summary": {
            "added_count": len(changes["added"]),
            "removed_count": len(changes["removed"]),
        },
        "details": changes  # 'changes' ahora es completamente serializable en JSON
    }