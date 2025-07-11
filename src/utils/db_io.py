from __future__ import annotations
import asyncio
import json
import logging
import os
from contextlib import nullcontext
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.dialects.postgresql import insert
from src.extensions import db, socketio
from src.models import LastUpdate, StockPrice, StockFilter, FilteredStockHistory
from src.utils.json_utils import (
    extract_timestamp_from_filename,
    get_latest_json_file,
)

logger = logging.getLogger(__name__)

def store_prices_in_db(data_object: Dict | List, market_timestamp: datetime, app=None, filtered_symbols: Optional[List[str]] = None) -> None:
    """
    Guarda precios desde un objeto en memoria en la DB usando operaciones masivas (bulk)
    y emite un evento `new_data`.
    """
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        try:
            rows = data_object.get("listaResult") if isinstance(data_object, dict) else data_object
            if not isinstance(rows, list):
                logger.warning("El objeto de datos no contiene una lista de resultados válida.")
                return

            ts = market_timestamp
            
            symbols_to_track = set(s.upper() for s in filtered_symbols) if filtered_symbols else None
            
            all_stock_data = []
            for item in rows:
                if not isinstance(item, dict): continue
                
                symbol = item.get('NEMO')
                if not symbol: continue

                if symbols_to_track and symbol.upper() not in symbols_to_track:
                    continue

                def safe_float(value):
                    if value is None: return None
                    try: return float(str(value).replace(",", "."))
                    except (ValueError, TypeError): return None
                
                def safe_int(value):
                    if value is None: return None
                    try: return int(value)
                    except (ValueError, TypeError): return None

                stock_price_obj = {
                    'symbol': symbol, 'timestamp': ts,
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
                all_stock_data.append(stock_price_obj)

            if not all_stock_data:
                logger.info("No hay datos de acciones válidos para guardar (o ninguno pasó el filtro).")
                lu = db.session.get(LastUpdate, 1) or LastUpdate(id=1)
                lu.timestamp = ts
                db.session.add(lu)
                db.session.commit()
                socketio.emit("new_data", {'message': 'Actualización completada, sin datos nuevos para guardar.'})
                return

            bind = db.session.get_bind()
            if bind.dialect.name == "postgresql":
                stmt = insert(StockPrice).values(all_stock_data)
                update_dict = {c.name: c for c in stmt.excluded if not c.primary_key}
                stmt = stmt.on_conflict_do_update(
                    index_elements=['symbol', 'timestamp'],
                    set_=update_dict
                )
                db.session.execute(stmt)
            else: # Fallback para SQLite
                db.session.bulk_insert_mappings(StockPrice, all_stock_data)
            
            lu = db.session.get(LastUpdate, 1) or LastUpdate(id=1)
            lu.timestamp = ts
            db.session.add(lu)
            db.session.commit()
            
            socketio.emit("new_data", {'message': 'Datos actualizados!'})
            logger.info(f"Datos guardados para {len(all_stock_data)} acciones con timestamp {ts.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            logger.exception("Error al guardar precios en la DB o emitir evento: %s", e)
            db.session.rollback()

def get_latest_data() -> Dict[str, Any]:
    """Devuelve los datos más recientes, priorizando la base de datos."""
    try:
        latest_update = db.session.query(db.func.max(StockPrice.timestamp)).scalar()
        if latest_update:
            prices = StockPrice.query.filter_by(timestamp=latest_update).all()
            return {"data": [p.to_dict() for p in prices], "timestamp": latest_update.strftime("%d/%m/%Y %H:%M:%S"), "source": "database"}

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
    latest_data = get_latest_data()
    if "error" in latest_data: return latest_data

    all_stocks = latest_data["data"]
    if not stock_codes:
        return { "data": all_stocks, "timestamp": latest_data["timestamp"], "source": latest_data["source"] }

    wanted_codes = {c.upper().strip() for c in stock_codes if c and isinstance(c, str)}
    filtered = [s for s in all_stocks if s.get('NEMO', '').upper().strip() in wanted_codes]
    
    return { "data": filtered, "timestamp": latest_data["timestamp"], "source": latest_data["source"] }


def compare_last_two_db_entries(stock_codes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Compara los dos últimos registros de precios en la DB, filtrando opcionalmente."""
    try:
        timestamps = db.session.query(StockPrice.timestamp).distinct().order_by(StockPrice.timestamp.desc()).limit(2).all()
        if len(timestamps) < 2: return None

        ts_curr, ts_prev = timestamps[0][0], timestamps[1][0]
        
        query_curr = StockPrice.query.filter_by(timestamp=ts_curr)
        query_prev = StockPrice.query.filter_by(timestamp=ts_prev)

        if stock_codes:
            query_curr = query_curr.filter(StockPrice.symbol.in_(stock_codes))
            query_prev = query_prev.filter(StockPrice.symbol.in_(stock_codes))
        
        curr_map = {r.symbol: r.to_dict() for r in query_curr.all()}
        prev_map = {r.symbol: r.to_dict() for r in query_prev.all()}

        new_syms = set(curr_map) - set(prev_map)
        removed_syms = set(prev_map) - set(curr_map)

        changes, unchanged = [], []
        for sym in curr_map.keys() & prev_map.keys():
            curr, prev = curr_map[sym], prev_map[sym]
            if curr.get("PRECIO_CIERRE") != prev.get("PRECIO_CIERRE") or curr.get("VARIACION") != prev.get("VARIACION"):
                diff = (curr.get('PRECIO_CIERRE') or 0) - (prev.get('PRECIO_CIERRE') or 0)
                pct = (diff / prev["PRECIO_CIERRE"] * 100) if prev.get("PRECIO_CIERRE") and prev.get("PRECIO_CIERRE") != 0 else 0.0
                changes.append({ "symbol": sym, "old": prev, "new": curr, "abs_diff": diff, "pct_diff": pct })
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

def save_filtered_comparison_history(market_timestamp: datetime, app=None):
    """Compara los últimos datos, filtra por StockFilter y guarda los cambios."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        market_hour, market_minute = market_timestamp.hour, market_timestamp.minute
        is_trading_hours = (market_hour == 9 and market_minute >= 30) or (market_hour > 9 and market_hour < 16)

        if not is_trading_hours:
            logger.info(f"Fuera de horario de mercado ({market_timestamp.strftime('%H:%M:%S')}). No se guardará historial.")
            return

        stock_filter = StockFilter.query.first()
        if not stock_filter or stock_filter.all or not stock_filter.codes_json:
            return

        try:
            stock_codes_to_track = json.loads(stock_filter.codes_json)
            if not stock_codes_to_track: return

            comparison = compare_last_two_db_entries(stock_codes=stock_codes_to_track)
            if not comparison or 'changes' not in comparison: return

            new_entries = [
                FilteredStockHistory(
                    timestamp=market_timestamp, symbol=change['symbol'],
                    price=change.get('new', {}).get('PRECIO_CIERRE'),
                    previous_price=change.get('old', {}).get('PRECIO_CIERRE'),
                    price_difference=change.get('abs_diff'), percent_change=change.get('pct_diff')
                ) for change in comparison.get('changes', [])
            ]
            
            if new_entries:
                db.session.bulk_save_objects(new_entries)
                db.session.commit()
                logger.info(f"✓ Guardados {len(new_entries)} registros en historial filtrado.")

        except Exception as e:
            logger.error(f"Error al guardar historial filtrado: {e}", exc_info=True)
            db.session.rollback()