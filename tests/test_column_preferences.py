import os
import pytest

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from src import main
from src.models import db
from src.models.column_preference import ColumnPreference

@pytest.fixture
def app():
    app = main.app
    with app.app_context():
        ColumnPreference.__table__.create(db.engine, checkfirst=True)
    yield app


def test_column_preferences(app):
    client = app.test_client()
    resp = client.get('/api/column-preferences')
    assert resp.status_code == 200
    assert resp.get_json()['columns'] is None

    resp = client.post('/api/column-preferences', json={'columns': ['A', 'B']})
    assert resp.status_code == 200

    resp = client.get('/api/column-preferences')
    assert resp.get_json()['columns'] == '["A", "B"]'
