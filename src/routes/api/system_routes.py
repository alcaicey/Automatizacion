# src/routes/api/system_routes.py
import logging
from flask import jsonify, request, current_app

from src.routes.api import api_bp 
from src.extensions import db
from src.models import LogEntry, Alert, FilteredStockHistory

logger = logging.getLogger(__name__)

@api_bp.route("/logs", methods=["GET", "POST"])
def handle_logs():
    with current_app.app_context():
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            log = LogEntry(level="INFO", message=data.get("message", ""), action=data.get("action", "frontend"))
            db.session.add(log)
            db.session.commit()
            return jsonify(log.to_dict()), 201
        
        if request.method == 'GET':
            query = LogEntry.query.order_by(LogEntry.timestamp.desc())
            search = request.args.get("q")
            if search:
                query = query.filter(LogEntry.message.ilike(f"%{search}%"))
            return jsonify([l.to_dict() for l in query.limit(200).all()])

@api_bp.route("/alerts", methods=["GET", "POST"])
def handle_alerts():
    with current_app.app_context():
        if request.method == 'POST':
            data = request.get_json() or {}
            try:
                alert = Alert(
                    symbol=data["symbol"].upper(),
                    target_price=float(data["target_price"]),
                    condition=data["condition"]
                )
                if alert.condition not in {"above", "below"}: raise ValueError("Condición inválida")
                db.session.add(alert)
                db.session.commit()
                return jsonify(alert.to_dict()), 201
            except (KeyError, ValueError, TypeError):
                return jsonify({"error": "Datos de alerta inválidos."}), 400
        
        if request.method == 'GET':
            alerts = Alert.query.filter_by(triggered=False).all()
            return jsonify([a.to_dict() for a in alerts])