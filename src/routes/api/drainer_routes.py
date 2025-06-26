# src/routes/api/drainer_routes.py
import logging
import threading
from flask import jsonify, current_app

from . import api_bp
from src.scripts.drainer_service import run_drainer_analysis
from src.models import AnomalousEvent

logger = logging.getLogger(__name__)

@api_bp.route("/drainers/events", methods=["GET"])
def get_drainer_events():
    with current_app.app_context():
        events = AnomalousEvent.query.order_by(AnomalousEvent.event_date.desc()).all()
        return jsonify([event.to_dict() for event in events])

@api_bp.route("/drainers/analyze", methods=["POST"])
def trigger_drainer_analysis():
    def analysis_task(app):
        with app.app_context():
            run_drainer_analysis()

    app_instance = current_app._get_current_object()
    thread = threading.Thread(target=analysis_task, args=(app_instance,), daemon=True)
    thread.start()
    
    return jsonify({"message": "El análisis de adelantamientos ha comenzado."}), 202