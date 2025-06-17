from datetime import datetime, timedelta

from src.scripts.compare_prices import compare_prices
from src.models.stock_price import StockPrice
from src.extensions import db


def test_compare_prices_basic(app):
    with app.app_context():
        ts_prev = datetime.utcnow() - timedelta(days=1)
        ts_curr = datetime.utcnow()
        db.session.add(StockPrice(symbol="AAA", price=1, variation=0.1, timestamp=ts_prev))
        db.session.add(StockPrice(symbol="BBB", price=2, variation=0.0, timestamp=ts_prev))
        db.session.add(StockPrice(symbol="AAA", price=1.5, variation=0.2, timestamp=ts_curr))
        db.session.add(StockPrice(symbol="CCC", price=3, variation=0.0, timestamp=ts_curr))
        db.session.commit()

        result = compare_prices(app)
        nuevos = {r["symbol"] for r in result["nuevos"]}
        eliminados = {r["symbol"] for r in result["eliminados"]}
        cambios = {r["symbol"] for r in result["cambios"]}

        assert "CCC" in nuevos
        assert "BBB" in eliminados
        assert "AAA" in cambios
