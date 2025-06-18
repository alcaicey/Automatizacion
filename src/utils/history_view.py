import os
import json
import glob
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.config import LOGS_DIR
from src.utils.db_io import compare_last_two_db_entries
from src.utils.json_utils import extract_timestamp_from_filename
from src.extensions import db
from src.models.stock_price import StockPrice

logger = logging.getLogger(__name__)


def _parse_file(path: str) -> Dict[str, Any]:
    # (Esta función parece correcta, la dejamos como está)
    # ...
    return {} # Placeholder

def _history_from_db() -> List[Dict[str, Any]]:
    """Construye un resumen del historial de cargas utilizando los registros de la base de datos."""
    try:
        timestamps_query = db.session.query(StockPrice.timestamp).distinct().order_by(StockPrice.timestamp).all()
        if len(timestamps_query) < 2:
            return []

        timestamps = [ts[0] for ts in timestamps_query]
        history: List[Dict[str, Any]] = []

        for i in range(1, len(timestamps)):
            ts_curr = timestamps[i]
            ts_prev = timestamps[i-1]
            
            curr_rows = StockPrice.query.filter_by(timestamp=ts_curr).all()
            prev_rows = StockPrice.query.filter_by(timestamp=ts_prev).all()

            # --- INICIO DE LA CORRECCIÓN: Usar los nombres de atributo del modelo, no del diccionario ---
            curr_map = {r.symbol: r for r in curr_rows}
            prev_map = {r.symbol: r for r in prev_rows}
            # --- FIN DE LA CORRECCIÓN ---
            
            curr_symbols = set(curr_map.keys())
            prev_symbols = set(prev_map.keys())
                
            new = len(curr_symbols - prev_symbols)
            removed = len(prev_symbols - curr_symbols)
            
            changes = 0
            for sym in curr_symbols & prev_symbols:
                # --- INICIO DE LA CORRECCIÓN: Comparar atributos del objeto, no claves del diccionario ---
                if curr_map[sym].price != prev_map[sym].price or curr_map[sym].variation != prev_map[sym].variation:
                    changes += 1
                # --- FIN DE LA CORRECCIÓN ---

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

        history.sort(key=lambda x: datetime.fromisoformat(x["file"]), reverse=True)
        return history
    except Exception as e:
        logger.error(f"Error al construir historial desde DB: {e}", exc_info=True)
        return []


def load_history(logs_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Devuelve una lista de resúmenes del historial de cargas, priorizando la base de datos.
    """
    try:
        db_history = _history_from_db()
        if db_history:
            return db_history
    except Exception as e:
        logger.warning(f"No se pudo cargar el historial desde la DB. Recurriendo a archivos. Error: {e}")

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


def compare_latest(logs_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Compara los dos últimos estados de datos, priorizando la base de datos.
    """
    try:
        db_comparison = compare_last_two_db_entries()
        if db_comparison:
            return db_comparison
    except Exception as e:
        logger.warning(f"No se pudo comparar desde la DB. Recurriendo a archivos. Error: {e}")

    logs_dir = logs_dir or LOGS_DIR
    pattern = os.path.join(logs_dir, 'acciones-precios-plus_*.json')
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    if len(files) < 2:
        return {}

    prev_file, curr_file = files[-2], files[-1]
    prev_data = _parse_file(prev_file)
    curr_data = _parse_file(curr_file)
    
    prev_map = prev_data['map']
    curr_map = curr_data['map']
    prev_symbols = set(prev_map.keys())
    curr_symbols = set(curr_map.keys())
    
    new_syms = [curr_map[s] for s in curr_symbols - prev_symbols]
    removed_syms = [prev_map[s] for s in prev_symbols - curr_symbols]
    
    changes, unchanged = [], []
    for sym in curr_symbols & prev_symbols:
        curr_item, prev_item = curr_map[sym], prev_map[sym]
        if curr_item['price'] != prev_item['price']:
            diff = curr_item['price'] - prev_item['price']
            pct = (diff / prev_item['price'] * 100) if prev_item['price'] != 0 else 0.0
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