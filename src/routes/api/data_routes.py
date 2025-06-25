# src/routes/api/data_routes.py
import logging
from flask import jsonify, request, current_app
from sqlalchemy import select, and_, func

# --- INICIO DE LA CORRECCIÓN ---
# Importa el objeto `api_bp` desde el __init__.py del paquete actual (la carpeta 'api')
from . import api_bp
# --- FIN DE LA CORRECCIÓN ---

from src.utils.db_io import get_latest_data, filter_stocks, compare_last_two_db_entries
from src.utils import history_view
from src.extensions import db
from src.models import (
    StockPrice, Dividend, StockClosing, AdvancedKPI, KpiSelection, FilteredStockHistory
)

logger = logging.getLogger(__name__)

# A partir de aquí, el resto del archivo no necesita cambios, ya que usa el `api_bp` importado.
@api_bp.route("/stocks", methods=["GET"])
def get_stocks():
    with current_app.app_context():
        stock_codes = request.args.getlist("code")
        result = filter_stocks(stock_codes) if stock_codes else get_latest_data()
        return jsonify(result)

@api_bp.route("/history", methods=["GET"])
def history_list():
    with current_app.app_context():
        return jsonify(history_view.load_history())

@api_bp.route("/history/compare", methods=["GET"])
def history_compare():
    with current_app.app_context():
        stock_codes = request.args.getlist("code")
        comparison_data = compare_last_two_db_entries(stock_codes=stock_codes if stock_codes else None)
        return jsonify(comparison_data or history_view.compare_latest(stock_codes=stock_codes if stock_codes else None) or {})

@api_bp.route("/stocks/history/<symbol>", methods=["GET"])
def stock_history(symbol):
    with current_app.app_context():
        prices = db.session.query(StockPrice).filter_by(symbol=symbol.upper()).order_by(StockPrice.timestamp).all()
        labels = [p.timestamp.strftime("%d/%m/%Y %H:%M:%S") for p in prices]
        data = [p.price for p in prices]
        return jsonify({"labels": labels, "data": data})

@api_bp.route("/dividends", methods=["GET"])
def get_dividends():
    with current_app.app_context():
        latest_closing_date = db.session.query(func.max(StockClosing.date)).scalar()
        if not latest_closing_date:
            dividends = Dividend.query.order_by(Dividend.payment_date.asc()).all()
            results = [d.to_dict() for d in dividends]
            for r in results:
                r['is_ipsa'] = False
            return jsonify(results)
        results = db.session.query(
            Dividend, StockClosing.belongs_to_ipsa
        ).outerjoin(
            StockClosing, and_(Dividend.nemo == StockClosing.nemo, StockClosing.date == latest_closing_date)
        ).order_by(Dividend.payment_date.asc()).all()
        enriched_dividends = []
        for dividend, belongs_to_ipsa in results:
            dividend_dict = dividend.to_dict()
            dividend_dict['is_ipsa'] = bool(belongs_to_ipsa) 
            enriched_dividends.append(dividend_dict)
        return jsonify(enriched_dividends)

@api_bp.route("/closing", methods=["GET"])
def get_closing_data():
    with current_app.app_context():
        nemos_to_filter = request.args.getlist("nemo")
        latest_date = db.session.query(func.max(StockClosing.date)).scalar()
        if not latest_date: return jsonify([])
        query = StockClosing.query.filter_by(date=latest_date)
        if nemos_to_filter:
            logger.info(f"[API /closing] Filtrando Cierre Bursátil por: {nemos_to_filter}")
            query = query.filter(StockClosing.nemo.in_(nemos_to_filter))
        closings = query.order_by(StockClosing.nemo).all()
        return jsonify([c.to_dict() for c in closings])

@api_bp.route("/kpis", methods=["GET"])
def get_all_kpis():
    with current_app.app_context():
        selected_nemos_query = select(KpiSelection.nemo)
        selected_nemos = [row.nemo for row in db.session.execute(selected_nemos_query).all()]
        if not selected_nemos: return jsonify([])
        latest_date = db.session.query(func.max(StockClosing.date)).scalar()
        if not latest_date: return jsonify([])
        closings = StockClosing.query.filter(StockClosing.nemo.in_(selected_nemos), StockClosing.date == latest_date).all()
        advanced_kpis = {k.nemo: k.to_dict() for k in AdvancedKPI.query.filter(AdvancedKPI.nemo.in_(selected_nemos)).all()}
        combined_data = []
        for closing in closings:
            data = closing.to_dict()
            adv_data = advanced_kpis.get(data['nemo'], {})
            data['roe'] = adv_data.get('roe')
            data['debt_to_equity'] = adv_data.get('debt_to_equity')
            data['beta'] = adv_data.get('beta')
            data['riesgo'] = adv_data.get('analyst_recommendation')
            data['dividend_yield'] = data.get('ren_actual')
            data['kpi_last_updated'] = adv_data.get('last_updated')
            data['kpi_source'] = adv_data.get('source')
            combined_data.append(data)
        return jsonify(combined_data)

@api_bp.route("/dashboard/chart-data", methods=["GET"])
def get_dashboard_chart_data():
    with current_app.app_context():
        from datetime import datetime, timedelta, timezone
        stock_symbols = request.args.getlist("stock")
        metric = request.args.get("metric", "price")
        days_history = request.args.get("days", 30, type=int)
        
        if not stock_symbols: return jsonify({"error": "Debe especificar al menos un símbolo."}), 400
        
        valid_metrics = {
            "price": FilteredStockHistory.price,
            "price_difference": FilteredStockHistory.price_difference,
            "percent_change": FilteredStockHistory.percent_change
        }
        if metric not in valid_metrics: return jsonify({"error": "Métrica no válida."}), 400
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days_history)
        history_data = db.session.query(
            FilteredStockHistory.symbol, FilteredStockHistory.timestamp, valid_metrics[metric]
        ).filter(
            FilteredStockHistory.symbol.in_(stock_symbols),
            FilteredStockHistory.timestamp >= start_date
        ).order_by(FilteredStockHistory.timestamp).all()

        chart_data = {symbol: [] for symbol in stock_symbols}
        for symbol, timestamp, value in history_data:
            if value is not None:
                chart_data[symbol].append({"x": timestamp.isoformat(), "y": value})
        
        return jsonify(chart_data)