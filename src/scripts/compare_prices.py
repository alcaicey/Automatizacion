import json
import os
from typing import Any, Dict, List, Tuple
from contextlib import nullcontext

from src.models import db
from src.models.stock_price import StockPrice


# --- Helpers -----------------------------------------------------------------

def _parse_json(path: str) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse a JSON file of stock prices and detect per-item errors."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = data.get("listaResult") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        rows = []

    mapping: Dict[str, Dict[str, Any]] = {}
    errors: List[Dict[str, Any]] = []

    for item in rows:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol") or item.get("NEMO")
        price = item.get("price") if item.get("price") is not None else item.get("PRECIO_CIERRE")
        variation = item.get("variation") if item.get("variation") is not None else item.get("VARIACION")
        missing: List[str] = []
        if not symbol:
            missing.append("symbol")
        if price is None:
            missing.append("price")
        if missing:
            errors.append({"symbol": symbol or "", "errors": missing})
            continue
        try:
            price_f = float(price)
        except (TypeError, ValueError):
            price_f = 0.0
        try:
            variation_f = float(variation) if variation is not None else 0.0
        except (TypeError, ValueError):
            variation_f = 0.0
        mapping[symbol] = {
            "symbol": symbol,
            "price": price_f,
            "variation": variation_f,
        }
    return mapping, errors


def _load_latest_db_data() -> Tuple[str | None, Dict[str, Dict[str, Any]]]:
    """Return timestamp and mapping of latest stock prices from DB."""
    last = StockPrice.query.order_by(StockPrice.timestamp.desc()).first()
    if not last:
        return None, {}
    ts = last.timestamp
    rows = StockPrice.query.filter_by(timestamp=ts).all()
    return ts.isoformat() if ts else None, {r.symbol: {"symbol": r.symbol, "price": r.price, "variation": r.variation} for r in rows}


# --- Public API ---------------------------------------------------------------

def compare_prices(json_path: str, sample_path: str | None = None, app=None) -> Dict[str, Any]:
    """Compare a JSON file of prices against the latest records stored in DB."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        ts_db, db_data = _load_latest_db_data()
        if not db_data and sample_path and os.path.exists(sample_path):
            db_data, _ = _parse_json(sample_path)

        file_data, errors = _parse_json(json_path)

        file_syms = set(file_data)
        db_syms = set(db_data)

        nuevos = [file_data[s] for s in file_syms - db_syms]
        eliminados = [db_data[s] for s in db_syms - file_syms]
        cambios: List[Dict[str, Any]] = []
        for sym in file_syms & db_syms:
            curr = file_data[sym]
            prev = db_data[sym]
            if curr["price"] != prev["price"] or curr["variation"] != prev["variation"]:
                cambios.append({"symbol": sym, "old": prev, "new": curr})

        return {
            "nuevos": nuevos,
            "eliminados": eliminados,
            "cambios": cambios,
            "errores": errors,
            "timestamp_db": ts_db,
        }
