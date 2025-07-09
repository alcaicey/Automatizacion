# src/routes/api/drainer_routes.py
import logging
import threading
from flask import jsonify, current_app, Blueprint

from src.tasks import run_drainer_analysis_task
from src.models import AnomalousEvent

logger = logging.getLogger(__name__)
drainer_bp = Blueprint('drainer', __name__)

@drainer_bp.route("/drainers/events", methods=["GET"])
def get_drainer_events():
    with current_app.app_context():
        events = AnomalousEvent.query.order_by(AnomalousEvent.event_date.desc()).all()
        return jsonify([event.to_dict() for event in events])

@drainer_bp.route('/analyze', methods=['POST'])
def analyze_drainer():
    """
    Encola una tarea de Celery para ejecutar el análisis de adelantamientos (drainer).
    Devuelve una respuesta inmediata con el ID de la tarea.
    """
    task = run_drainer_analysis_task.delay()
    return jsonify({
        "message": "El análisis de adelantamientos ha sido encolado.",
        "task_id": task.id
    }), 202