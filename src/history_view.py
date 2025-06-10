import os
import json
import glob
from typing import List, Dict, Any
from datetime import datetime

from src.config import LOGS_DIR
from src.scripts.bolsa_service import extract_timestamp_from_filename


def _parse_file(path: str) -> Dict[str, Any]:
    """Return parsed items with error detection."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    rows = raw.get('listaResult') if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        rows = []
    items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        symbol = item.get('symbol') or item.get('NEMO') or ''
        price = item.get('price')
        if price is None:
            price = item.get('PRECIO_CIERRE')
        variation = item.get('variation')
        if variation is None:
            variation = item.get('VARIACION')
        ts = item.get('timestamp')
        try:
            price = float(price)
        except (TypeError, ValueError):
            price = 0.0
        try:
            variation = float(variation)
        except (TypeError, ValueError):
            variation = 0.0
        errs = []
        if not symbol:
            errs.append('symbol')
        if ts in (None, ''):
            errs.append('timestamp')
        if errs:
            errors.append({'symbol': symbol, 'errors': errs})
            # Skip invalid records entirely
            continue
        entry = {
            'symbol': symbol,
            'price': price,
            'variation': variation,
            'timestamp': ts,
        }
        items.append(entry)
        mapping[symbol] = entry

    ts_str = extract_timestamp_from_filename(path)
    return {'items': items, 'map': mapping, 'errors': errors, 'timestamp': ts_str}


def load_history(logs_dir: str | None = None) -> List[Dict[str, Any]]:
    """Return list of historical load summaries sorted by date descending."""
    logs_dir = logs_dir or LOGS_DIR
    pattern = os.path.join(logs_dir, 'acciones-precios-plus_*.json')
    files = sorted(glob.glob(pattern))
    history: List[Dict[str, Any]] = []
    prev_symbols: set[str] = set()
    prev_data: Dict[str, Any] | None = None
    for path in files:
        parsed = _parse_file(path)
        symbols = set(parsed['map'])
        new_syms = symbols - prev_symbols if prev_symbols else set()
        removed_syms = prev_symbols - symbols if prev_symbols else set()
        changes = []
        if prev_data:
            for sym in symbols & prev_symbols:
                curr = parsed['map'][sym]
                prev = prev_data['map'][sym]
                if curr['price'] != prev['price'] or curr['variation'] != prev['variation']:
                    changes.append(sym)
        status = 'OK'
        if parsed['errors']:
            status = 'con errores'
        elif not new_syms and not removed_syms and not changes:
            status = 'sin cambios'
        history.append({
            'file': os.path.basename(path),
            'timestamp': parsed['timestamp'],
            'total': len(symbols),
            'changes': len(changes),
            'new': len(new_syms),
            'removed': len(removed_syms),
            'error_count': len(parsed['errors']),
            'status': status,
        })
        prev_symbols = symbols
        prev_data = parsed
    history.sort(key=lambda x: datetime.strptime(x['timestamp'], '%d/%m/%Y %H:%M:%S'), reverse=True)
    return history


def compare_latest(logs_dir: str | None = None) -> Dict[str, Any]:
    """Return comparison details between the last and previous loads."""
    logs_dir = logs_dir or LOGS_DIR
    pattern = os.path.join(logs_dir, 'acciones-precios-plus_*.json')
    files = sorted(glob.glob(pattern))
    if len(files) < 2:
        return {}
    prev_file, curr_file = files[-2], files[-1]
    prev_data = _parse_file(prev_file)
    curr_data = _parse_file(curr_file)
    prev_symbols = set(prev_data['map'])
    curr_symbols = set(curr_data['map'])
    new_syms = curr_symbols - prev_symbols
    removed_syms = prev_symbols - curr_symbols
    changes: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    for sym in curr_symbols & prev_symbols:
        curr = curr_data['map'][sym]
        prev = prev_data['map'][sym]
        if curr['price'] != prev['price']:
            diff = curr['price'] - prev['price']
            pct = (diff / prev['price'] * 100) if prev['price'] else 0.0
            changes.append({
                'symbol': sym,
                'old': prev,
                'new': curr,
                'abs_diff': diff,
                'pct_diff': pct,
            })
        else:
            unchanged.append(curr)
    return {
        'current_file': os.path.basename(curr_file),
        'previous_file': os.path.basename(prev_file),
        'current_timestamp': curr_data['timestamp'],
        'previous_timestamp': prev_data['timestamp'],
        'new': [curr_data['map'][s] for s in new_syms],
        'removed': [prev_data['map'][s] for s in removed_syms],
        'changes': changes,
        'unchanged': unchanged,
        'errors': curr_data['errors'] + prev_data['errors'],
        'total_compared': len(curr_symbols | prev_symbols),
        'change_count': len(changes),
    }
