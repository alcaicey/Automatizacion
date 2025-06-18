import os
import json
import glob
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from itertools import groupby

from src.config import LOGS_DIR
from src.utils.db_io import compare_last_two_db_entries
from src.utils.json_utils import extract_timestamp_from_filename, get_latest_json_file
from src.extensions import db
from src.models.stock_price import StockPrice

logger = logging.getLogger(__name__)


def _parse_file(path: str) -> Dict[str, Any]:
    """
    Parsea un archivo JSON de precios. Esta es una función de fallback si la DB falla.
    NOTA: La implementación completa de esta función dependería del formato exacto
    de los archivos JSON guardados si se decidiera usarla.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Asume que el JSON es una lista de diccionarios o un dict con 'listaResult'
        rows = data.get("listaResult") if isinstance(data, dict) else data
        if not isinstance(rows, list):
            return {'map': {}, 'errors': ['Formato de JSON no válido'], 'timestamp': ''}

        price_map = {item.get('NEMO'): {'price': item.get('PRECIO_CIERRE')} for item in rows if item.get('NEMO')}
        return {
            'map': price_map,
            'errors': [],
            'timestamp': extract_timestamp_from_filename(path)
        }
    except Exception as e:
        logger.error(f"Error parseando archivo {path}: {e}")
        return {'map': {}, 'errors': [str(e)], 'timestamp': ''}


def _history_from_db() -> List[Dict[str, Any]]:
    """
    Construye un resumen del historial de cargas de forma eficiente, haciendo una
    sola consulta a la base de datos.
    """
    try:
        # 1. Obtener todos los registros de una vez, ordenados por fecha
        all_prices = StockPrice.query.order_by(StockPrice.timestamp).all()
        if not all_prices:
            return []

        # 2. Agrupar los registros por timestamp en un diccionario
        data_by_ts = {
            ts: list(items) for ts, items in groupby(all_prices, key=lambda p: p.timestamp)
        }
        
        timestamps = sorted(data_by_ts.keys())
        if len(timestamps) < 2:
            return []

        history: List[Dict[str, Any]] = []

        # 3. Iterar sobre los timestamps para comparar los datos ya cargados en memoria
        for i in range(1, len(timestamps)):
            ts_curr, ts_prev = timestamps[i], timestamps[i-1]
            
            curr_rows = data_by_ts[ts_curr]
            prev_rows = data_by_ts[ts_prev]

            curr_map = {r.symbol: r for r in curr_rows}
            prev_map = {r.symbol: r for r in prev_rows}
            
            curr_symbols = set(curr_map.keys())
            prev_symbols = set(prev_map.keys())
                
            new = len(curr_symbols - prev_symbols)
            removed = len(prev_symbols - curr_symbols)
            
            changes = 0
            for sym in curr_symbols & prev_symbols:
                # Comparamos los atributos directamente desde los objetos del modelo
                if curr_map[sym].price != prev_map[sym].price or curr_map[sym].variation != prev_map[sym].variation:
                    changes += 1

            status = "OK"
            if not new and not removed and not changes:
                status = "Sin cambios"

            history.append({
                "file": ts_curr.isoformat(),
                "timestamp": ts_curr.strftime("%d/%m/%Y %H:%M:%S"),
                "total": len(curr_map),
                "changes": changes,
                "new": new,
                "removed": removed,
                "error_count": 0,
                "status": status,
            })
        
        # Ordenar el resultado final para mostrar lo más reciente primero
        history.sort(key=lambda x: x["file"], reverse=True)
        return history

    except Exception as e:
        logger.error(f"Error al construir historial desde DB: {e}", exc_info=True)
        return []


def load_history(logs_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Devuelve una lista de resúmenes del historial de cargas, priorizando la base de datos.
    Si la base de datos falla, recurre a los archivos JSON como fallback.
    """
    try:
        db_history = _history_from_db()
        # Solo usamos la historia de la DB si tiene contenido
        if db_history:
            return db_history
    except Exception as e:
        logger.warning(f"No se pudo cargar el historial desde la DB. Recurriendo a archivos. Error: {e}")

    # --- Fallback a archivos JSON si la DB no devuelve historial ---
    logs_dir = logs_dir or LOGS_DIR
    pattern = os.path.join(logs_dir, 'acciones-precios-plus_*.json')
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    
    history: List[Dict[str, Any]] = []
    prev_data: Optional[Dict[str, Any]] = None

    for path in files:
        parsed = _parse_file(path)
        symbols = set(parsed['map'].keys())
        
        changes, new, removed = 0, 0, 0
        if prev_data:
            prev_symbols = set(prev_data['map'].keys())
            new = len(symbols - prev_symbols)
            removed = len(prev_symbols - symbols)
            for sym in symbols & prev_symbols:
                if parsed['map'][sym]['price'] != prev_data['map'][sym]['price']:
                    changes += 1

        status = 'OK'
        if parsed['errors']:
            status = 'Con errores'
        elif prev_data and not new and not removed and not changes:
            status = 'Sin cambios'
            
        history.append({
            'file': os.path.basename(path),
            'timestamp': parsed['timestamp'],
            'total': len(symbols),
            'changes': changes,
            'new': new,
            'removed': removed,
            'error_count': len(parsed['errors']),
            'status': status,
        })
        prev_data = parsed
        
    history.reverse()
    return history


def compare_latest(stock_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Compara los dos últimos estados de datos, priorizando la base de datos.
    Si la DB falla, recurre a archivos JSON.
    """
    try:
        # Pasa los códigos de acciones a la función de comparación de la DB
        db_comparison = compare_last_two_db_entries(stock_codes=stock_codes)
        if db_comparison:
            return db_comparison
    except Exception as e:
        logger.warning(f"No se pudo comparar desde la DB. Recurriendo a archivos. Error: {e}")

    # --- Fallback a archivos JSON ---
    pattern = os.path.join(LOGS_DIR, 'acciones-precios-plus_*.json')
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    if len(files) < 2:
        return {}

    prev_file, curr_file = files[-2], files[-1]
    prev_data = _parse_file(prev_file)
    curr_data = _parse_file(curr_file)
    
    prev_map = prev_data['map']
    curr_map = curr_data['map']

    # Filtrar por códigos si se proporcionan
    if stock_codes:
        wanted = {c.upper().strip() for c in stock_codes}
        prev_map = {k: v for k, v in prev_map.items() if k in wanted}
        curr_map = {k: v for k, v in curr_map.items() if k in wanted}

    prev_symbols = set(prev_map.keys())
    curr_symbols = set(curr_map.keys())
    
    new_syms = [curr_map[s] for s in curr_symbols - prev_symbols]
    removed_syms = [prev_map[s] for s in prev_symbols - curr_symbols]
    
    changes, unchanged = [], []
    for sym in curr_symbols & prev_symbols:
        curr_item, prev_item = curr_map[sym], prev_map[sym]
        if curr_item['price'] != prev_item['price']:
            price_curr = curr_item.get('price') or 0
            price_prev = prev_item.get('price') or 0
            diff = price_curr - price_prev
            pct = (diff / price_prev * 100) if price_prev != 0 else 0.0
            changes.append({'symbol': sym, 'old': prev_item, 'new': curr_item, 'abs_diff': diff, 'pct_diff': pct})
        else:
            unchanged.append(curr_item)
            
    return {
        'current_timestamp': curr_data['timestamp'],
        'previous_timestamp': prev_data['timestamp'],
        'new': new_syms,
        'removed': removed_syms,
        'changes': changes,
        'unchanged': unchanged,
        'errors': curr_data['errors'] + prev_data['errors'],
    }