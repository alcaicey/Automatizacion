from datetime import datetime, timedelta
from src.routes import errors as errors_module
from src.models.log_entry import LogEntry
from src.extensions import db


def test_error_log_pagination(app):
    with app.app_context():
        # create sample error logs with different timestamps
        now = datetime.utcnow()
        for i in range(3):
            entry = LogEntry(
                level="ERROR",
                message=f"err{i}",
                action="test",
                timestamp=now - timedelta(minutes=i),
            )
            db.session.add(entry)
        db.session.commit()
    client = app.test_client()
    resp = client.get("/api/error-logs?offset=1&limit=1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["message"] == "err1"
