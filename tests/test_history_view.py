from datetime import datetime

from src import history_view
from src.models.stock_price import StockPrice
from src.models import db


def test_load_and_compare(app):
    ts1 = datetime(2024, 1, 1, 12, 0, 0)
    ts2 = datetime(2024, 1, 2, 12, 0, 0)
    with app.app_context():
        db.session.add_all([
            StockPrice(symbol="AAA", price=1, variation=0.0, timestamp=ts1),
            StockPrice(symbol="BBB", price=2, variation=0.1, timestamp=ts1),
        ])
        db.session.add_all([
            StockPrice(symbol="AAA", price=1.5, variation=0.2, timestamp=ts2),
            StockPrice(symbol="CCC", price=3, variation=0.0, timestamp=ts2),
        ])
        db.session.commit()

        history = history_view.load_history()
        assert len(history) == 2
        assert history[0]["total"] == 2

        cmp = history_view.compare_latest()
        assert len(cmp["new"]) == 1
        assert cmp["new"][0]["symbol"] == "CCC"
        assert len(cmp["removed"]) == 1
        assert cmp["removed"][0]["symbol"] == "BBB"
        assert len(cmp["changes"]) == 1
        assert cmp["changes"][0]["symbol"] == "AAA"
