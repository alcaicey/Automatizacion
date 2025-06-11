import logging
import traceback
from flask import Blueprint, jsonify, request
from src.models.log_entry import LogEntry
from src.models import db

errors_bp = Blueprint('errors', __name__)
logger = logging.getLogger(__name__)


def log_error(source: str, message: str, stack: str | None = None) -> LogEntry:
    """Persist an error log entry in the database and log via logger."""
    logger.error(f"[{source}] {message}")
    entry = LogEntry(level='ERROR', message=message, action=source, stack=stack)
    db.session.add(entry)
    db.session.commit()
    return entry


@errors_bp.route('/error-logs', methods=['GET'])
def list_error_logs():
    """Return paginated error logs ordered by most recent."""
    offset = request.args.get('offset', default=0, type=int)
    limit = request.args.get('limit', default=100, type=int)
    query = LogEntry.query.filter_by(level='ERROR').order_by(LogEntry.timestamp.desc())
    logs = query.offset(offset).limit(limit).all()
    return jsonify([log.to_dict() for log in logs])
