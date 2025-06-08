import json
import threading

import pytest

from src.scripts import bolsa_service

from src.extensions import socketio


def test_filter_endpoint_launches_browser(app, tmp_path, monkeypatch):
    """Browser should launch when filtering stocks if no cached data exists."""
    data = {
        "listaResult": [{"NEMO": "FIL", "PRECIO_CIERRE": 10, "VARIACION": 0.1}]
    }
    json_path = tmp_path / "acciones-precios-plus_20240104_000000.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    calls = []

    def fake_run(app=None, non_interactive=True):
        calls.append(True)
        if app:
            with app.app_context():
                bolsa_service.store_prices_in_db(str(json_path), app=app)
        return str(json_path)

    monkeypatch.setattr("src.routes.api.run_bolsa_bot", fake_run)
    monkeypatch.setattr(bolsa_service, "run_bolsa_bot", fake_run)
    monkeypatch.setattr(bolsa_service, "get_latest_json_file", lambda: None)

    client = app.test_client()
    resp = client.get("/api/stocks?code=FIL")
    assert resp.status_code == 200
    assert calls


def test_update_endpoint_launches_browser(app, tmp_path, monkeypatch):
    """Browser should launch when manual update is requested."""
    data = {"listaResult": [{"NEMO": "UPD", "PRECIO_CIERRE": 20, "VARIACION": 0.2}]}
    json_path = tmp_path / "acciones-precios-plus_20240105_000000.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    calls = []

    def fake_run(app=None, non_interactive=True):
        calls.append(True)
        if app:
            with app.app_context():
                bolsa_service.store_prices_in_db(str(json_path), app=app)
        return str(json_path)

    monkeypatch.setattr("src.routes.api.run_bolsa_bot", fake_run)
    monkeypatch.setattr(bolsa_service, "run_bolsa_bot", fake_run)

    class DummyThread:
        def __init__(self, target, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(threading, "Thread", DummyThread)

    ws_client = socketio.test_client(app)
    client = app.test_client()
    resp = client.post("/api/stocks/update")
    assert resp.status_code == 200
    assert calls
    received = ws_client.get_received()
    assert any(r["name"] == "new_data" for r in received)
