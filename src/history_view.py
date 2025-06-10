from typing import List, Dict, Any
from datetime import datetime

from src.models import db
from src.models.stock_price import StockPrice


def _query_items(ts) -> List[StockPrice]:
    return StockPrice.query.filter_by(timestamp=ts).all()


def _row_to_dict(row: StockPrice) -> Dict[str, Any]:
    return {
        "symbol": row.symbol,
        "price": row.price,
        "variation": row.variation,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
    }


def _validate_row(row: StockPrice) -> List[str]:
    errs = []
    if not row.symbol:
        errs.append("symbol")
    if row.timestamp is None:
        errs.append("timestamp")
    if row.price == 0.0:
        errs.append("price")
    return errs


def load_history() -> List[Dict[str, Any]]:
    """Return list of historical summaries sorted by timestamp descending."""
    timestamps = [r[0] for r in db.session.query(StockPrice.timestamp).distinct().order_by(StockPrice.timestamp).all()]
    history: List[Dict[str, Any]] = []
    prev_map: Dict[str, StockPrice] = {}
    for ts in timestamps:
        rows = _query_items(ts)
        curr_map = {r.symbol: r for r in rows}
        symbols = set(curr_map)
        prev_symbols = set(prev_map)
        new_syms = symbols - prev_symbols if prev_map else set()
        removed_syms = prev_symbols - symbols if prev_map else set()
        changes = []
        for sym in symbols & prev_symbols:
            c = curr_map[sym]
            p = prev_map[sym]
            if c.price != p.price or c.variation != p.variation:
                changes.append(sym)
        errors = [
            {"symbol": r.symbol, "errors": _validate_row(r)}
            for r in rows
            if _validate_row(r)
        ]
        status = "OK"
        if errors:
            status = "con errores"
        elif not new_syms and not removed_syms and not changes:
            status = "sin cambios"
        history.append({
            "timestamp": ts.strftime("%d/%m/%Y %H:%M:%S"),
            "total": len(rows),
            "changes": len(changes),
            "new": len(new_syms),
            "removed": len(removed_syms),
            "error_count": len(errors),
            "status": status,
        })
        prev_map = curr_map
    history.sort(key=lambda x: datetime.strptime(x["timestamp"], "%d/%m/%Y %H:%M:%S"), reverse=True)
    return history


def compare_latest() -> Dict[str, Any]:
    """Return comparison between the last two timestamps."""
    timestamps = [r[0] for r in db.session.query(StockPrice.timestamp).distinct().order_by(StockPrice.timestamp).all()]
    if len(timestamps) < 2:
        return {}
    prev_ts, curr_ts = timestamps[-2], timestamps[-1]
    prev_rows = {r.symbol: r for r in _query_items(prev_ts)}
    curr_rows = {r.symbol: r for r in _query_items(curr_ts)}
    prev_symbols = set(prev_rows)
    curr_symbols = set(curr_rows)
    new_syms = curr_symbols - prev_symbols
    removed_syms = prev_symbols - curr_symbols
    changes = []
    unchanged = []
    errors = []
    for r in _query_items(curr_ts):
        errs = _validate_row(r)
        if errs:
            errors.append({"symbol": r.symbol, "errors": errs})
    for r in _query_items(prev_ts):
        errs = _validate_row(r)
        if errs:
            errors.append({"symbol": r.symbol, "errors": errs})
    for sym in curr_symbols & prev_symbols:
        c = curr_rows[sym]
        p = prev_rows[sym]
        if c.price != p.price or c.variation != p.variation:
            changes.append({"symbol": sym, "old": _row_to_dict(p), "new": _row_to_dict(c)})
        else:
            unchanged.append(_row_to_dict(c))
    return {
        "current_timestamp": curr_ts.strftime("%d/%m/%Y %H:%M:%S"),
        "previous_timestamp": prev_ts.strftime("%d/%m/%Y %H:%M:%S"),
        "new": [_row_to_dict(curr_rows[s]) for s in new_syms],
        "removed": [_row_to_dict(prev_rows[s]) for s in removed_syms],
        "changes": changes,
        "unchanged": unchanged,
        "errors": errors,
    }
