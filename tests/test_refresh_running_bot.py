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
