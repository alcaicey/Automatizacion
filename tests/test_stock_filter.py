import os
import pytest

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from src import main
from src.models import db
from src.models.stock_filter import StockFilter

@pytest.fixture
def app():
    app = main.app
    with app.app_context():
        StockFilter.__table__.create(db.engine, checkfirst=True)
    yield app


def test_stock_filter_endpoints(app):
    client = app.test_client()
    resp = client.get('/api/stock-filter')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['codes'] is None
    assert data['all'] is False

    resp = client.post('/api/stock-filter', json={'codes': ['A', 'B'], 'all': False})
    assert resp.status_code == 200

    resp = client.get('/api/stock-filter')
    data = resp.get_json()
    assert data['codes'] == '["A", "B"]'
    assert data['all'] is False

    resp = client.post('/api/stock-filter', json={'codes': [], 'all': True})
    assert resp.status_code == 200
    resp = client.get('/api/stock-filter')
    data = resp.get_json()
    assert data['codes'] == '[]'
    assert data['all'] is True
