import json
from datetime import datetime

from src.scripts import bolsa_service
from src.models.last_update import LastUpdate
from src.models.stock_price import StockPrice
from src.utils.extensions import socketio


def test_last_update_sync(app, tmp_path):
    ts = datetime(2025, 6, 9, 17, 29, 57)
    json_path = tmp_path / f"acciones-precios-plus_{ts.strftime('%Y%m%d_%H%M%S')}.json"
    data = {"listaResult": [{"NEMO": "AAA", "PRECIO_CIERRE": 1, "VARIACION": 0.1}]}
    json_path.write_text(json.dumps(data), encoding="utf-8")

    client = socketio.test_client(app)
    with app.app_context():
        bolsa_service.store_prices_in_db(str(json_path), ts, app=app)
        lu = LastUpdate.query.get(1)
        assert lu is not None
        assert lu.timestamp == ts
        result = bolsa_service.get_latest_data()
        assert result["timestamp"] == ts.strftime("%d/%m/%Y %H:%M:%S")
        prices = StockPrice.query.filter_by(timestamp=ts).all()
        assert len(prices) == 1

    received = client.get_received()
    assert any(r["name"] == "new_data" for r in received)
