# src/routes/api/portfolio_routes.py
import logging
import json
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.models import Portfolio, KpiSelection, StockClosing, PortfolioColumnPreference
from src.extensions import db

# 1. Crea un Blueprint específico para este módulo
portfolio_bp = Blueprint('portfolio_bp', __name__)

logger = logging.getLogger(__name__)

# 2. Usa ESE blueprint para decorar las rutas
@portfolio_bp.route("/", methods=["GET", "POST"])
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

@portfolio_bp.route("/<int:holding_id>", methods=["DELETE"])
def delete_from_portfolio(holding_id):
    with current_app.app_context():
        holding = db.session.get(Portfolio, holding_id)
        if not holding: return jsonify({"error": "Registro no encontrado en el portafolio."}), 404
        db.session.delete(holding)
        db.session.commit()
        return '', 204

@portfolio_bp.route('/view', methods=['GET'])
def get_portfolio_data_view():
    """
    Retorna una vista completa de datos del portafolio, combinando holdings
    con los precios de cierre más recientes y calculando un resumen.
    """
    try:
        holdings = Portfolio.query.order_by(Portfolio.symbol).all()
        
        symbols = [h.symbol for h in holdings]
        if not symbols:
            return jsonify({"portfolio": [], "summary": {
                "total_paid": 0, "total_current_value": 0, "total_gain_loss": 0
            }})

        latest_prices = {}
        for symbol in symbols:
            price_entry = StockClosing.query.filter_by(nemo=symbol).order_by(StockClosing.date.desc()).first()
            if price_entry:
                latest_prices[symbol] = {"price": price_entry.previous_day_close_price}
            else:
                latest_prices[symbol] = {"price": 0}
        
        portfolio_data = []
        total_paid = 0
        total_current_value = 0

        for h in holdings:
            price_info = latest_prices.get(h.symbol, {"price": 0})
            current_price = price_info["price"]
            
            paid_value = h.quantity * h.purchase_price
            current_value = h.quantity * current_price
            gain_loss = current_value - paid_value
            gain_loss_percent = (gain_loss / paid_value) * 100 if paid_value > 0 else 0

            portfolio_data.append({
                "id": h.id,
                "symbol": h.symbol,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
                "total_paid": paid_value,
                "current_price": current_price,
                "daily_variation_percent": 0,
                "current_value": current_value,
                "gain_loss_total": gain_loss,
                "gain_loss_percent": gain_loss_percent,
                "actions": f'<button class="btn btn-sm btn-danger delete-holding-btn" data-id="{h.id}"><i class="fas fa-trash"></i></button>'
            })
            total_paid += paid_value
            total_current_value += current_value

        summary = {
            "total_paid": total_paid,
            "total_current_value": total_current_value,
            "total_gain_loss": total_current_value - total_paid
        }
        
        return jsonify({"portfolio": portfolio_data, "summary": summary})

    except Exception as e:
        logger.error(f"Error al generar la vista de datos del portafolio: {e}")
        return jsonify({"error": "Error interno del servidor al procesar los datos del portafolio."}), 500

@portfolio_bp.route('/holdings', methods=['GET'])
def get_portfolio_holdings_alias():
    """Ruta alias para compatibilidad con el frontend. Llama a la vista principal."""
    return get_portfolio_data_view()

@portfolio_bp.route("/kpis/selection", methods=["GET", "POST"])
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

@portfolio_bp.route("/columns", methods=["GET", "POST"])
def handle_portfolio_columns():
    """Gestiona las preferencias de columnas para la tabla de Portafolio."""
    with current_app.app_context():
        if request.method == 'GET':
            all_cols = [
                'symbol', 'quantity', 'purchase_price', 'total_paid', 
                'current_price', 'daily_variation_percent', 'current_value',
                'gain_loss_total', 'gain_loss_percent', 'actions'
            ]
            prefs = PortfolioColumnPreference.query.first()
            visible_cols = json.loads(prefs.columns_json) if prefs and prefs.columns_json else all_cols
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data:
                return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(PortfolioColumnPreference, 1) or PortfolioColumnPreference(id=1) # type: ignore
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})