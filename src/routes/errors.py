import logging
import traceback
from flask import Blueprint
from src.models.log_entry import LogEntry
from src.extensions import db

errors_bp = Blueprint('errors', __name__)
logger = logging.getLogger(__name__)


def log_error(source: str, message: str, stack: str | None = None) -> None:
    """Persiste una entrada de log de error en la base de datos y la registra a través del logger."""
    logger.error(f"[{source}] {message}")
    try:
        entry = LogEntry(level='ERROR', message=message, action=source, stack=stack)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.critical(f"FALLO AL GUARDAR LOG DE ERROR EN DB: {e}", exc_info=True)
        db.session.rollback()