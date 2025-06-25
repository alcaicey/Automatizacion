# src/routes/api/portfolio_routes.py
import logging
from flask import jsonify, request, current_app
from sqlalchemy import select

from src.routes.api import api_bp 
from src.extensions import db
from src.models import Portfolio, KpiSelection, StockClosing

logger = logging.getLogger(__name__)

@api_bp.route("/portfolio", methods=["GET", "POST"])
def portfolio_handler():
    with current_app.app_context():
        if request.method == 'GET':
            holdings = Portfolio.query.order_by(Portfolio.symbol).all()
            return jsonify([h.to_dict() for h in holdings])
        
        if request.method == 'POST':
            data = request.get_json() or {}
            try:
                holding = Portfolio(
                    symbol=data["symbol"].upper(),
                    quantity=float(data["quantity"]),
                    purchase_price=float(data["purchase_price"])
                )
                db.session.add(holding)
                db.session.commit()
                return jsonify(holding.to_dict()), 201
            except (KeyError, ValueError, TypeError):
                return jsonify({"error": "Datos de portafolio inválidos."}), 400
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error de DB al añadir a portafolio: {e}")
                return jsonify({"error": "Error interno al guardar en la base de datos."}), 500

@api_bp.route("/portfolio/<int:holding_id>", methods=["DELETE"])
def delete_from_portfolio(holding_id):
    with current_app.app_context():
        holding = db.session.get(Portfolio, holding_id)
        if not holding: return jsonify({"error": "Registro no encontrado en el portafolio."}), 404
        db.session.delete(holding)
        db.session.commit()
        return '', 204

@api_bp.route("/kpis/selection", methods=["GET", "POST"])
def handle_kpi_selection():
    """Obtiene o actualiza la lista de acciones seleccionadas para KPIs."""
    with current_app.app_context():
        if request.method == "GET":
            all_closings_query = select(StockClosing.nemo).distinct().order_by(StockClosing.nemo)
            all_nemos = [row.nemo for row in db.session.execute(all_closings_query).all()]
            
            selected_nemos_query = select(KpiSelection.nemo)
            selected_nemos = {row.nemo for row in db.session.execute(selected_nemos_query).all()}
            
            result = [{"nemo": nemo, "is_selected": nemo in selected_nemos} for nemo in all_nemos]
            return jsonify(result)

        if request.method == "POST":
            data = request.get_json()
            if not isinstance(data, dict) or "nemos" not in data:
                return jsonify({"error": "Formato inválido. Se espera {'nemos': [...]}."}), 400
            
            KpiSelection.query.delete()
            
            new_selections = [KpiSelection(nemo=nemo) for nemo in data["nemos"]]
            db.session.add_all(new_selections)
            db.session.commit()
            return jsonify({"success": True, "message": f"Selección guardada con {len(new_selections)} acciones."})