import json

from src.scripts import bolsa_service
from src.models.stock_price import StockPrice


def test_store_prices_upsert(app, tmp_path):
    data = {
        "listaResult": [
            {"NEMO": "DUP", "PRECIO_CIERRE": 1, "VARIACION": 0.0}
        ]
    }
    json_path = tmp_path / "acciones-precios-plus_20240110_000000.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    with app.app_context():
        bolsa_service.store_prices_in_db(str(json_path))
        # Call again with the same data. Should not raise IntegrityError
        bolsa_service.store_prices_in_db(str(json_path))
        prices = StockPrice.query.all()

    assert len(prices) == 1
