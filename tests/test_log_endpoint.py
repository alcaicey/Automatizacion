from src.routes import api as api_module
from src.models.log_entry import LogEntry


def test_log_endpoint_writes_message(app):
    client = app.test_client()
    resp = client.post(
        "/api/logs",
        json={"message": "hello", "stack": "trace", "action": "test"},
    )
    assert resp.status_code == 201
    with app.app_context():
        entry = LogEntry.query.first()
        assert entry is not None
        assert entry.message == "hello"


def test_log_endpoint_requires_message(app):
    client = app.test_client()
    resp = client.post("/api/logs", json={})
    assert resp.status_code == 400
