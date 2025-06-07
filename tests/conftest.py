import os
import pytest

# Use in-memory SQLite for tests to avoid external DB
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from src import main
from src.models import db


@pytest.fixture
def app():
    """Create Flask app with in-memory database for tests."""
    app = main.app
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()
