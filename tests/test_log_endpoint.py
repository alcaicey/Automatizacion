import logging
from src.routes import api as api_module


def test_log_endpoint_writes_message(app, tmp_path):
    log_path = tmp_path / "frontend.log"
    # replace logger handlers
    for h in list(api_module.client_logger.handlers):
        api_module.client_logger.removeHandler(h)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    api_module.client_logger.addHandler(handler)
    api_module.client_logger.setLevel(logging.INFO)

    client = app.test_client()
    resp = client.post(
        "/api/logs",
        json={"message": "hello", "stack": "trace", "action": "test"},
    )
    handler.flush()
    assert resp.status_code == 201
    contents = log_path.read_text(encoding="utf-8")
    assert "hello" in contents
    assert "[test]" in contents


def test_log_endpoint_requires_message(app):
    client = app.test_client()
    resp = client.post("/api/logs", json={})
    assert resp.status_code == 400
