import json
from src.routes import api as api_module


def test_update_when_bot_running_triggers_enter(app, monkeypatch):
    called = {}
    monkeypatch.setattr(api_module, "is_bot_running", lambda: True)

    def fake_enter():
        called["enter"] = True
        return True

    monkeypatch.setattr("src.scripts.bolsa_service.send_enter_key_to_browser", fake_enter)

    client = app.test_client()
    resp = client.post("/api/stocks/update")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert called.get("enter")


def test_update_restarts_when_enter_fails(app, monkeypatch):
    monkeypatch.setattr(api_module, "is_bot_running", lambda: True)

    def fake_enter():
        return False

    run_called = {}

    def fake_run(app=None, non_interactive=None, keep_open=True):
        run_called["run"] = True

    monkeypatch.setattr(
        "src.scripts.bolsa_service.send_enter_key_to_browser", fake_enter
    )
    monkeypatch.setattr("src.routes.api.run_bolsa_bot", fake_run)

    class DummyThread:
        def __init__(self, target, args=(), kwargs=None):
            self.target = target
            self.kwargs = kwargs or {}

        def start(self):
            self.target(**self.kwargs)

    import threading as threading_module
    monkeypatch.setattr(threading_module, "Thread", DummyThread)

    client = app.test_client()
    resp = client.post("/api/stocks/update")
    assert resp.status_code == 200
    data = resp.get_json()
    assert run_called.get("run")
    assert "reiniciado" in data["message"].lower()
