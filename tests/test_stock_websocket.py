import json
import threading
from flask import has_app_context

import pytest

from src.utils.extensions import socketio
from src.models.stock_price import StockPrice
from src.scripts import bolsa_service


def test_store_prices_emits_event_and_saves(app, tmp_path):
    client = socketio.test_client(app)
    data = {
        "listaResult": [
            {
                "NEMO": "TEST",
                "PRECIO_CIERRE": 100,
                "VARIACION": 1.5,
            }
        ]
    }
    json_path = tmp_path / "acciones-precios-plus_20240101_000000.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    with app.app_context():
        bolsa_service.store_prices_in_db(str(json_path))
        prices = StockPrice.query.all()

    assert len(prices) == 1
    received = client.get_received()
    assert any(r["name"] == "new_data" for r in received)


def test_update_endpoint_triggers_websocket(app, tmp_path, monkeypatch):
    calls = []

    data = {
        "listaResult": [
            {"NEMO": "MOCK", "PRECIO_CIERRE": 50, "VARIACION": 0.1}
        ]
    }
    json_path = tmp_path / "acciones-precios-plus_20240102_000000.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    def fake_run(app=None, non_interactive=True, keep_open=True):
        calls.append(True)
        with app.app_context():
            bolsa_service.store_prices_in_db(str(json_path), app=app)
        return str(json_path)

    monkeypatch.setattr("src.routes.api.run_bolsa_bot", fake_run)

    class DummyThread:
        def __init__(self, target, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(threading, "Thread", DummyThread)

    ws_client = socketio.test_client(app)
    http_client = app.test_client()
    resp = http_client.post("/api/stocks/update")
    assert resp.status_code == 200
    assert calls

    with app.app_context():
        assert StockPrice.query.count() == 1

    received = ws_client.get_received()
    assert any(r["name"] == "new_data" for r in received)


def test_update_endpoint_uses_context(app, tmp_path, monkeypatch):
    data = {
        "listaResult": [
            {"NEMO": "CTX", "PRECIO_CIERRE": 10, "VARIACION": 0.2}
        ]
    }
    json_path = tmp_path / "acciones-precios-plus_20240103_000000.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    def fake_get_latest_json_file():
        return str(json_path)

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run_subprocess(*args, **kwargs):
        return Result()

    calls = {}
    original_store = bolsa_service.store_prices_in_db

    def wrapped_store(path, app=None):
        calls["called"] = True
        assert has_app_context()
        original_store(path, app=app)

    monkeypatch.setattr(bolsa_service, "get_latest_json_file", fake_get_latest_json_file)
    monkeypatch.setattr(bolsa_service.subprocess, "run", fake_run_subprocess)
    monkeypatch.setattr(bolsa_service, "store_prices_in_db", wrapped_store)

    monkeypatch.setenv("BOLSA_USERNAME", "u")
    monkeypatch.setenv("BOLSA_PASSWORD", "p")

    class DummyThread:
        def __init__(self, target, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(threading, "Thread", DummyThread)

    client = app.test_client()
    resp = client.post("/api/stocks/update")
    assert resp.status_code == 200
    assert calls.get("called")

    with app.app_context():
        assert StockPrice.query.count() == 1

