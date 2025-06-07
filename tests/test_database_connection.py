import os
import pytest
from sqlalchemy import create_engine, text

DB_URL = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')

if not DB_URL:
    pytest.skip('No database URL configured', allow_module_level=True)

SKIP_SQLITE_MEMORY = DB_URL == 'sqlite:///:memory:'

@pytest.mark.skipif(SKIP_SQLITE_MEMORY, reason="In-memory SQLite used for tests")
def test_database_connection():
    """Ensure the configured database is reachable."""
    engine = create_engine(DB_URL)
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1'))
            assert result.scalar() == 1
    except Exception as exc:
        pytest.fail(f"PostgreSQL is unreachable: {exc}")
