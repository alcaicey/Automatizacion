import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # noqa: E402

# Ensure database is sqlite for tests
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from src import main
from src.models import db
from src.models.user import User

@pytest.fixture
def app():
    app = main.app
    with app.app_context():
        User.__table__.create(db.engine, checkfirst=True)
    yield app


def test_get_users_endpoint(app):
    client = app.test_client()
    resp = client.get('/api/users')
    assert resp.status_code == 200
