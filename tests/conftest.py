import os

# Use in-memory SQLite for tests to avoid external DB
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
