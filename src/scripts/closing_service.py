# src/scripts/closing_service.py

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from sqlalchemy.dialects.postgresql import insert

from src.extensions import db
from src.models import StockClosing

logger = logging.getLogger(__name__)

CLOSING_PAGE_URL = "https://www.bolsadesantiago.com/cierre_bursatil"
CLOSING_API_PATTERN = "api/RV_ResumenMercado/getCierreBursatilAnterior"

class DataCaptureError(Exception): pass

async def fetch_closing_data_with_playwright(page: Page) -> List[Dict[str, Any]] | None:
    """Navega a la página de Cierre Bursátil e intercepta la respuesta de la API."""
    logger.info("[ClosingService] Navegando a la página de Cierre Bursátil...")
    
    if CLOSING_PAGE_URL not in page.url:
         await page.goto(CLOSING_PAGE_URL, wait_until="domcontentloaded", timeout=30000)

    try:
        async with page.expect_response(lambda r: CLOSING_API_PATTERN in r.url, timeout=25000) as response_info:
            logger.info("[ClosingService] Listener de red activo. Recargando para capturar datos...")
            await page.reload(wait_until="domcontentloaded", timeout=25000)
        
        response = await response_info.value
        data = await response.json()
        if "listaResult" in data and isinstance(data["listaResult"], list):
            logger.info(f"✓ API de Cierre Bursátil interceptada con {len(data['listaResult'])} registros.")
            return data["listaResult"]
        
        raise DataCaptureError("El formato de la respuesta de la API no es el esperado.")

    except PlaywrightTimeoutError:
        raise DataCaptureError("Timeout esperando la respuesta de la API de Cierre Bursátil.") from None
    except Exception as e:
        raise DataCaptureError(f"Error inesperado durante la captura: {e}") from e

def _process_api_item(item: Dict[str, Any]) -> Dict[str, Any] | None:
    """Convierte un item de la API a un formato limpio y validado para la DB."""
    try:
        return {
            "date": datetime.strptime(item["fec_fij_cie"], "%Y-%m-%d").date(),
            "nemo": item["nemo"],
            "previous_day_amount": item.get("monto_ant"),
            "previous_day_trades": item.get("neg_ant"),
            "previous_day_close_price": item.get("precio_cierre_ant"),
            "belongs_to_igpa": bool(item.get("PERTENECE_IGPA")),
            "belongs_to_ipsa": bool(item.get("PERTENECE_IPSA")),
            "weight_igpa": item.get("PESO_IGPA"),
            "weight_ipsa": item.get("PESO_IPSA"),
            "price_to_earnings_ratio": item.get("razon_pre_uti"),
            "current_yield": item.get("ren_actual"),
            "previous_day_traded_units": item.get("un_transadas_ant"),
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Omitiendo registro de cierre mal formado: {item}. Error: {e}")
        return None

async def update_stock_closings(page: Page) -> Dict[str, Any]:
    """Obtiene los datos de cierre y los actualiza en la DB usando una estrategia de 'upsert'."""
    raw_data = await fetch_closing_data_with_playwright(page)
    if not raw_data:
        return {"error": "No se recibieron datos de la API.", "processed_count": 0}

    processed_data = [d for d in (_process_api_item(item) for item in raw_data) if d]
    if not processed_data:
        return {"error": "Ningún registro pudo ser procesado.", "processed_count": 0}
        
    try:
        # Usamos la sentencia 'INSERT ... ON CONFLICT DO UPDATE' de PostgreSQL para un "upsert" eficiente.
        stmt = insert(StockClosing).values(processed_data)
        
        update_dict = {c.name: c for c in stmt.excluded if not c.primary_key}
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['date', 'nemo'], # La PK compuesta
            set_=update_dict
        )
        
        db.session.execute(stmt)
        db.session.commit()
        
        processed_count = len(processed_data)
        logger.info(f"✓ Base de datos de Cierre Bursátil actualizada con {processed_count} registros.")
        return {"processed_count": processed_count}

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al hacer upsert en la tabla de Cierre Bursátil: {e}", exc_info=True)
        return {"error": f"Error de base de datos: {str(e)}", "processed_count": 0}