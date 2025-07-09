# src/utils/db_logging.py
import logging
from src.models.log_entry import LogEntry
from src.extensions import db

logger = logging.getLogger(__name__)

def log_error_to_db(source: str, message: str, stack: str | None = None) -> None:
    """Persiste una entrada de log de error en la base de datos y la registra a través del logger."""
    logger.error(f"[{source}] {message} - Stack: {stack}")
    try:
        # SQLAlchemy models are fine with keyword arguments, this is the correct way.
        entry = LogEntry(level='ERROR', message=message, action=source, stack=stack)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.critical(f"CRITICAL FAILURE: Could not write error log to database: {e}", exc_info=True)
        db.session.rollback() 