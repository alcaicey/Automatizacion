from __future__ import annotations
import asyncio
import json
import logging
import os
import re
import traceback
from contextlib import nullcontext
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.dialects.postgresql import insert

from src.extensions import db, socketio
from src.models import LastUpdate, StockPrice
from src.routes.errors import log_error
from src.utils.json_utils import (
    extract_timestamp_from_filename,
    get_latest_json_file,
)

logger = logging.getLogger(__name__)


def store_prices_in_db(data_object: Dict | List, market_timestamp: datetime, app=None) -> None:
    """
    Guarda precios desde un objeto de datos en memoria directamente en la DB
    y emite un evento `new_data`.
    """
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        try:
            # Los datos ya no se leen de un archivo, se reciben en 'data_object'
            rows = data_object.get("listaResult") if isinstance(data_object, dict) else data_object
            if not isinstance(rows, list):
                logger.warning("El objeto de datos no contiene una lista de resultados válida.")
                return

            ts = market_timestamp

            for item in rows:
                if not isinstance(item, dict): continue
                
                symbol = item.get('NEMO')
                if not symbol: continue

                def safe_float(value):
                    if value is None: return None
                    try: return float(str(value).replace(",", "."))
                    except (ValueError, TypeError): return None
                
                def safe_int(value):
                    if value is None: return None
                    try: return int(value)
                    except (ValueError, TypeError): return None

                stock_price_obj = {
                    'symbol': symbol,
                    'timestamp': ts,
                    'price': safe_float(item.get('PRECIO_CIERRE')),
                    'variation': safe_float(item.get('VARIACION')),
                    'buy_price': safe_float(item.get('PRECIO_COMPRA')),
                    'sell_price': safe_float(item.get('PRECIO_VENTA')),
                    'amount': safe_int(item.get('MONTO')),
                    'traded_units': safe_int(item.get('UN_TRANSADAS')),
                    'currency': item.get('MONEDA'),
                    'isin': item.get('ISIN'),
                    'green_bond': item.get('BONO_VERDE')
                }
                
                bind = db.session.get_bind()
                if bind.dialect.name == "postgresql":
                    stmt = insert(StockPrice).values(**stock_price_obj)
                    update_dict = {k: v for k, v in stock_price_obj.items() if k not in ['symbol', 'timestamp'] and v is not None}
                    if update_dict:
                        update_stmt = stmt.on_conflict_do_update(
                            index_elements=['symbol', 'timestamp'],
                            set_=update_dict
                        )
                        db.session.execute(update_stmt)
                    else:
                        db.session.execute(stmt.on_conflict_do_nothing(index_elements=['symbol', 'timestamp']))
                else:
                    db.session.merge(StockPrice(**stock_price_obj))

            lu = db.session.get(LastUpdate, 1) or LastUpdate(id=1)
            lu.timestamp = ts
            db.session.add(lu)
            db.session.commit()
            
            socketio.emit("new_data", {'message': 'Datos actualizados!'})
            logger.info(f"Datos guardados con timestamp del mercado {ts.strftime('%Y-%m-%d %H:%M:%S')} y evento 'new_data' emitido.")

        except Exception as e:
            logger.exception("Error al guardar precios en la DB o emitir evento: %s", e)
            db.session.rollback()


def get_latest_data() -> Dict[str, Any]:
    """
    Devuelve los datos más recientes. Prioriza la base de datos.
    Como fallback, busca el último archivo JSON si existe.
    """
    try:
        latest_update = db.session.query(db.func.max(StockPrice.timestamp)).scalar()
        if latest_update:
            prices = StockPrice.query.filter_by(timestamp=latest_update).all()
            translated_data = [p.to_dict() for p in prices]
            return {"data": translated_data, "timestamp": latest_update.strftime("%d/%m/%Y %H:%M:%S"), "source": "database"}

        # Fallback a archivos si la base de datos está vacía
        latest_json_path = get_latest_json_file()
        if latest_json_path and os.path.exists(latest_json_path):
            with open(latest_json_path, encoding="utf-8") as f:
                data_content = json.load(f)
            rows = data_content.get("listaResult", data_content if isinstance(data_content, list) else [])
            return { "data": rows, "timestamp": extract_timestamp_from_filename(latest_json_path), "source": f"file_fallback:{os.path.basename(latest_json_path)}" }

        return {"error": "No hay datos disponibles.", "data": [], "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    except Exception as exc:
        logger.exception("Error crítico en get_latest_data: %s", exc)
        return {"error": str(exc), "data": [], "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}


def filter_stocks(stock_codes: List[str]) -> Dict[str, Any]:
    """Filtra la lista de acciones por sus códigos (NEMO)."""
    try:
        latest_data = get_latest_data()
        if "error" in latest_data:
            return latest_data

        all_stocks = latest_data["data"]
        if not stock_codes:
            return { "data": all_stocks, "timestamp": latest_data["timestamp"], "source": latest_data["source"] }

        wanted_codes = {c.upper().strip() for c in stock_codes if c and isinstance(c, str)}
        filtered = [s for s in all_stocks if s.get('NEMO', '').upper().strip() in wanted_codes]
        
        return { "data": filtered, "timestamp": latest_data["timestamp"], "source": latest_data["source"] }
    except Exception as e:
        logger.exception("Error en filter_stocks: %s", e)
        return {"error": str(e), "data": [], "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}


def compare_last_two_db_entries(stock_codes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Compara los dos últimos registros de precios en la base de datos,
    filtrando por códigos de acción si se proporcionan.
    """
    try:
        timestamps = (
            db.session.query(StockPrice.timestamp)
            .distinct()
            .order_by(StockPrice.timestamp.desc())
            .limit(2)
            .all()
        )
        if len(timestamps) < 2: return None

        ts_curr, ts_prev = timestamps[0][0], timestamps[1][0]
        
        query_curr = StockPrice.query.filter_by(timestamp=ts_curr)
        query_prev = StockPrice.query.filter_by(timestamp=ts_prev)

        if stock_codes:
            query_curr = query_curr.filter(StockPrice.symbol.in_(stock_codes))
            query_prev = query_prev.filter(StockPrice.symbol.in_(stock_codes))
        
        curr_rows = query_curr.all()
        prev_rows = query_prev.all()

        curr_map = {r.symbol: {'symbol': r.symbol, 'price': r.price, 'variation': r.variation} for r in curr_rows}
        prev_map = {r.symbol: {'symbol': r.symbol, 'price': r.price, 'variation': r.variation} for r in prev_rows}

        new_syms = set(curr_map) - set(prev_map)
        removed_syms = set(prev_map) - set(curr_map)

        changes, unchanged = [], []
        for sym in curr_map.keys() & prev_map.keys():
            curr, prev = curr_map[sym], prev_map[sym]
            if curr.get("price") != prev.get("price") or curr.get("variation") != prev.get("variation"):
                diff = (curr.get('price') or 0) - (prev.get('price') or 0)
                pct = (diff / prev["price"] * 100) if prev.get("price") and prev.get("price") != 0 else 0.0
                changes.append({
                    "symbol": sym, "old": prev, "new": curr,
                    "abs_diff": diff, "pct_diff": pct,
                })
            else:
                unchanged.append(curr)

        return {
            "current_timestamp": ts_curr.strftime("%d/%m/%Y %H:%M:%S"),
            "previous_timestamp": ts_prev.strftime("%d/%m/%Y %H:%M:%S"),
            "new": [curr_map[s] for s in new_syms],
            "removed": [prev_map[s] for s in removed_syms],
            "changes": changes,
            "unchanged": unchanged,
        }
    except Exception as exc:
        logger.exception("Error comparando históricos desde la DB: %s", exc)
        return None