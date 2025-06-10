from typing import Any, Dict, List, Tuple
from contextlib import nullcontext

from src.models import db
from src.models.stock_price import StockPrice



def _load_last_two_db_entries() -> Tuple[
    str | None,
    str | None,
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    """Return mappings for the last two timestamps stored in DB."""
    timestamps = (
        db.session.query(StockPrice.timestamp)
        .distinct()
        .order_by(StockPrice.timestamp.desc())
        .limit(2)
        .all()
    )
    if len(timestamps) < 2:
        return None, None, {}, {}
    ts_curr, ts_prev = timestamps[0][0], timestamps[1][0]
    curr_rows = StockPrice.query.filter_by(timestamp=ts_curr).all()
    prev_rows = StockPrice.query.filter_by(timestamp=ts_prev).all()
    curr_map = {r.symbol: {"symbol": r.symbol, "price": r.price, "variation": r.variation} for r in curr_rows}
    prev_map = {r.symbol: {"symbol": r.symbol, "price": r.price, "variation": r.variation} for r in prev_rows}
    return ts_prev.isoformat(), ts_curr.isoformat(), prev_map, curr_map


# --- Public API ---------------------------------------------------------------

def compare_prices(app=None) -> Dict[str, Any]:
    """Compare the last two sets of prices stored in the database."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        ts_prev, ts_curr, prev_map, curr_map = _load_last_two_db_entries()
        if not prev_map or not curr_map:
            return {}

        prev_syms = set(prev_map)
        curr_syms = set(curr_map)

        nuevos = [curr_map[s] for s in curr_syms - prev_syms]
        eliminados = [prev_map[s] for s in prev_syms - curr_syms]
        cambios: List[Dict[str, Any]] = []
        for sym in curr_syms & prev_syms:
            curr = curr_map[sym]
            prev = prev_map[sym]
            if curr["price"] != prev["price"] or curr["variation"] != prev["variation"]:
                cambios.append({"symbol": sym, "old": prev, "new": curr})

        return {
            "previous_timestamp": ts_prev,
            "current_timestamp": ts_curr,
            "nuevos": nuevos,
            "eliminados": eliminados,
            "cambios": cambios,
            "errores": [],
        }
