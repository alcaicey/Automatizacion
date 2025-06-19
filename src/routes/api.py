import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, current_app

from src.scripts.bolsa_service import run_bolsa_bot
from src.utils.db_io import get_latest_data, filter_stocks, compare_last_two_db_entries
from src.utils.scheduler import start_periodic_updates, stop_periodic_updates
from src.models import Credential, LogEntry, ColumnPreference, StockFilter, StockPrice, Alert, FilteredStockHistory
from src.extensions import db
from ..utils import history_view
from sqlalchemy import func

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)
_sync_bot_running_lock = threading.Lock()

@api_bp.route("/bot-status", methods=["GET"])
def bot_status():
    is_running = _sync_bot_running_lock.locked()
    return jsonify({"is_running": is_running})

@api_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    if not _sync_bot_running_lock.acquire(blocking=False):
        return jsonify({"success": False, "message": "Ya hay una actualización en curso."}), 409
    
    app_instance = current_app._get_current_object()
    
    # Leemos las credenciales del entorno en el hilo principal
    username = os.getenv("BOLSA_USERNAME")
    password = os.getenv("BOLSA_PASSWORD")
    
    bot_kwargs = {
        "app": app_instance,
        "username": username,
        "password": password
    }

    def target_func(app):
        try:
            with app.app_context():
                loop = app.bot_event_loop
                future = asyncio.run_coroutine_threadsafe(run_bolsa_bot(**bot_kwargs), loop)
                future.result(timeout=300)
        finally:
            _sync_bot_running_lock.release()
            logger.info("[API] Lock liberado.")
    threading.Thread(target=target_func, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización iniciado."})

# ... (resto de los endpoints sin cambios) ...
_sync_bot_running_lock = threading.Lock()

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

# --- INICIO DE LA CORRECCIÓN: Pasar los filtros a la función de comparación ---
@api_bp.route("/history/compare", methods=["GET"])
def history_compare():
    with current_app.app_context():
        stock_codes = request.args.getlist("code")
        # Llama a la función de comparación de la base de datos con los códigos
        comparison_data = compare_last_two_db_entries(stock_codes=stock_codes if stock_codes else None)
        # Si la DB no devuelve nada, intenta el fallback a los archivos JSON
        return jsonify(comparison_data or history_view.compare_latest(stock_codes=stock_codes if stock_codes else None) or {})
# --- FIN DE LA CORRECCIÓN ---


@api_bp.route("/stocks/history/<symbol>", methods=["GET"])
def stock_history(symbol):
    """Retorna el historial completo de precios para un símbolo."""
    with current_app.app_context():
        prices = (
            db.session.query(StockPrice)
            .filter_by(symbol=symbol.upper())
            .order_by(StockPrice.timestamp)
            .all()
        )
        labels = [p.timestamp.strftime("%d/%m/%Y %H:%M:%S") for p in prices]
        data = [p.price for p in prices]
        return jsonify({"labels": labels, "data": data})

@api_bp.route("/columns", methods=["GET", "POST"])
def handle_columns():
    with current_app.app_context():
        if request.method == 'GET':
            latest_data = get_latest_data()
            all_cols = []
            if latest_data and latest_data.get('data'):
                all_cols = list(latest_data['data'][0].keys())

            if not all_cols: 
                all_cols = ['NEMO', 'PRECIO_CIERRE', 'VARIACION', 'timestamp']
            
            prefs = ColumnPreference.query.first()
            if prefs and prefs.columns_json:
                visible_cols = json.loads(prefs.columns_json)
            else:
                visible_cols = [col for col in ['NEMO', 'PRECIO_CIERRE', 'VARIACION', 'timestamp'] if col in all_cols]
            
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data:
                return jsonify({'error': 'Falta la lista de columnas'}), 400
            
            prefs = db.session.get(ColumnPreference, 1) or ColumnPreference(id=1)
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@api_bp.route("/filters", methods=["GET", "POST"])
def handle_filters():
    with current_app.app_context():
        if request.method == 'GET':
            stock_filter = StockFilter.query.first()
            if stock_filter:
                codes = json.loads(stock_filter.codes_json) if stock_filter.codes_json else []
                return jsonify({'codes': codes, 'all': stock_filter.all})
            return jsonify({'codes': [], 'all': True})

        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No se recibieron datos'}), 400
            
            stock_filter = db.session.get(StockFilter, 1) or StockFilter(id=1)
            stock_filter.codes_json = json.dumps(data.get('codes', []))
            stock_filter.all = data.get('all', False)
            db.session.add(stock_filter)
            db.session.commit()
            return jsonify({'success': True})

@api_bp.route("/credentials", methods=["GET", "POST"])
def handle_credentials():
    with current_app.app_context():
        if request.method == 'GET':
            cred = Credential.query.first()
            has_creds = bool(cred or (os.getenv("BOLSA_USERNAME") and os.getenv("BOLSA_PASSWORD")))
            return jsonify({"has_credentials": has_creds})
        else:
            data = request.get_json() or {}
            username = data.get("username")
            password = data.get("password")
            if not username or not password:
                return jsonify({"error": "Faltan credenciales."}), 400
            
            os.environ["BOLSA_USERNAME"] = username
            os.environ["BOLSA_PASSWORD"] = password
            
            if bool(data.get("remember")):
                cred = db.session.get(Credential, 1) or Credential(id=1)
                cred.username, cred.password = username, password
                db.session.add(cred)
            else:
                Credential.query.delete()
            db.session.commit()
            return jsonify({"success": True})

@api_bp.route("/logs", methods=["GET", "POST"])
def handle_logs():
    with current_app.app_context():
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            log = LogEntry(level="INFO", message=data.get("message", ""), action=data.get("action", "frontend"))
            db.session.add(log)
            db.session.commit()
            return jsonify(log.to_dict()), 201
        else:
            query = LogEntry.query.order_by(LogEntry.timestamp.desc())
            search = request.args.get("q")
            if search:
                query = query.filter(LogEntry.message.ilike(f"%{search}%"))
            return jsonify([l.to_dict() for l in query.limit(200).all()])

@api_bp.route("/alerts", methods=["POST"])
def create_alert():
    """Crea una nueva alerta de precios."""
    with current_app.app_context():
        data = request.get_json() or {}
        symbol = data.get("symbol", "").upper()
        target_price = data.get("target_price")
        condition = data.get("condition")
        if not symbol or target_price is None or condition not in {"above", "below"}:
            return jsonify({"error": "Datos de alerta incompletos."}), 400
        alert = Alert(symbol=symbol, target_price=float(target_price), condition=condition)
        db.session.add(alert)
        db.session.commit()
        return jsonify(alert.to_dict()), 201

@api_bp.route("/alerts", methods=["GET"])
def list_alerts():
    """Obtiene alertas pendientes."""
import asyncio
import json
import logging
import os
import threading
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app

from src.scripts.bolsa_service import run_bolsa_bot
from src.utils.db_io import get_latest_data, filter_stocks, compare_last_two_db_entries
from src.models import Alert
from src.utils.scheduler import start_periodic_updates, stop_periodic_updates
from src.models import Credential, LogEntry, ColumnPreference, StockFilter, StockPrice
from src.extensions import db
from ..utils import history_view

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)
_sync_bot_running_lock = threading.Lock()

@api_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    if not _sync_bot_running_lock.acquire(blocking=False):
        return jsonify({"success": False, "message": "Ya hay una actualización en curso."}), 409
    
    app_instance = current_app._get_current_object()
    username = os.getenv("BOLSA_USERNAME")
    password = os.getenv("BOLSA_PASSWORD")
    bot_kwargs = {"app": app_instance, "username": username, "password": password}

    def target_func(app):
        try:
            with app.app_context():
                loop = app.bot_event_loop
                future = asyncio.run_coroutine_threadsafe(run_bolsa_bot(**bot_kwargs), loop)
                future.result(timeout=300)
        finally:
            _sync_bot_running_lock.release()

    threading.Thread(target=target_func, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización iniciado."})

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

# --- INICIO DE LA CORRECCIÓN: Pasar los filtros a la función de comparación ---
@api_bp.route("/history/compare", methods=["GET"])
def history_compare():
    with current_app.app_context():
        stock_codes = request.args.getlist("code")
        comparison_data = compare_last_two_db_entries(stock_codes=stock_codes if stock_codes else None)
        # El fallback a history_view se mantiene por si se quieren comparar archivos JSON en el futuro
        return jsonify(comparison_data or history_view.compare_latest(stock_codes=stock_codes if stock_codes else None) or {})
# --- FIN DE LA CORRECCIÓN ---

@api_bp.route("/stocks/history/<symbol>", methods=["GET"])
def stock_history(symbol):
    with current_app.app_context():
        prices = db.session.query(StockPrice).filter_by(symbol=symbol.upper()).order_by(StockPrice.timestamp).all()
        labels = [p.timestamp.strftime("%d/%m/%Y %H:%M:%S") for p in prices]
        data = [p.price for p in prices]
        return jsonify({"labels": labels, "data": data})

@api_bp.route("/columns", methods=["GET", "POST"])
def handle_columns():
    with current_app.app_context():
        if request.method == 'GET':
            latest_data = get_latest_data()
            all_cols = list(latest_data['data'][0].keys()) if latest_data.get('data') else ['NEMO', 'PRECIO_CIERRE', 'VARIACION', 'timestamp']
            prefs = ColumnPreference.query.first()
            visible_cols = json.loads(prefs.columns_json) if prefs and prefs.columns_json else [col for col in ['NEMO', 'PRECIO_CIERRE', 'VARIACION', 'timestamp'] if col in all_cols]
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        if request.method == 'POST':
            data = request.get_json()
            prefs = db.session.get(ColumnPreference, 1) or ColumnPreference(id=1)
            prefs.columns_json = json.dumps(data.get('columns', []))
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@api_bp.route("/filters", methods=["GET", "POST"])
def handle_filters():
    with current_app.app_context():
        if request.method == 'GET':
            stock_filter = StockFilter.query.first()
            if stock_filter:
                codes = json.loads(stock_filter.codes_json) if stock_filter.codes_json else []
                return jsonify({'codes': codes, 'all': stock_filter.all})
            return jsonify({'codes': [], 'all': True})
        if request.method == 'POST':
            data = request.get_json()
            stock_filter = db.session.get(StockFilter, 1) or StockFilter(id=1)
            stock_filter.codes_json = json.dumps(data.get('codes', []))
            stock_filter.all = data.get('all', False)
            db.session.add(stock_filter)
            db.session.commit()
            return jsonify({'success': True})

@api_bp.route("/credentials", methods=["GET", "POST"])
def handle_credentials():
    with current_app.app_context():
        if request.method == 'GET':
            cred = Credential.query.first()
            return jsonify({"has_credentials": bool(cred or (os.getenv("BOLSA_USERNAME") and os.getenv("BOLSA_PASSWORD")))})
        else:
            data = request.get_json()
            os.environ["BOLSA_USERNAME"] = data.get("username", "")
            os.environ["BOLSA_PASSWORD"] = data.get("password", "")
            if bool(data.get("remember")):
                cred = db.session.get(Credential, 1) or Credential(id=1)
                cred.username, cred.password = data["username"], data["password"]
                db.session.add(cred)
            else: Credential.query.delete()
            db.session.commit()
            return jsonify({"success": True})

@api_bp.route("/logs", methods=["GET", "POST"])
def handle_logs():
    with current_app.app_context():
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            log = LogEntry(level="INFO", message=data.get("message", ""), action=data.get("action", "frontend"))
            db.session.add(log)
            db.session.commit()
            return jsonify(log.to_dict()), 201
        else:
            query = LogEntry.query.order_by(LogEntry.timestamp.desc())
            search = request.args.get("q")
            if search: query = query.filter(LogEntry.message.ilike(f"%{search}%"))
            return jsonify([l.to_dict() for l in query.limit(200).all()])

@api_bp.route("/alerts", methods=["POST", "GET"])
def handle_alerts():
    with current_app.app_context():
        if request.method == 'POST':
            data = request.get_json() or {}
            symbol, target_price, condition = data.get("symbol", "").upper(), data.get("target_price"), data.get("condition")
            if not all([symbol, target_price is not None, condition in {"above", "below"}]):
                return jsonify({"error": "Datos de alerta incompletos."}), 400
            alert = Alert(symbol=symbol, target_price=float(target_price), condition=condition)
            db.session.add(alert)
            db.session.commit()
            return jsonify(alert.to_dict()), 201
        if request.method == 'GET':
            alerts = Alert.query.filter_by(triggered=False).all()
            return jsonify([a.to_dict() for a in alerts])
    with current_app.app_context():
        alerts = Alert.query.filter_by(triggered=False).all()
        return jsonify([a.to_dict() for a in alerts])
# ... (importaciones existentes al principio del archivo)
# --- INICIO DE CORRECCIÓN: Asegúrate de importar el nuevo modelo ---
from src.models import Alert, Credential, LogEntry, ColumnPreference, StockFilter, StockPrice, Portfolio
# --- FIN DE CORRECCIÓN ---
# ... (resto del código de api.py)


# --- INICIO DE CORRECCIÓN: Nuevos Endpoints para el Portafolio ---

@api_bp.route("/portfolio", methods=["GET"])
def get_portfolio():
    """Obtiene todas las acciones guardadas en el portafolio."""
    with current_app.app_context():
        holdings = Portfolio.query.order_by(Portfolio.symbol).all()
        return jsonify([h.to_dict() for h in holdings])

@api_bp.route("/portfolio", methods=["POST"])
def add_to_portfolio():
    """Añade una nueva acción al portafolio."""
    with current_app.app_context():
        data = request.get_json() or {}
        symbol = data.get("symbol", "").upper()
        quantity = data.get("quantity")
        purchase_price = data.get("purchase_price")

        if not symbol or quantity is None or purchase_price is None:
            return jsonify({"error": "Datos incompletos: se requiere símbolo, cantidad y precio."}), 400

        try:
            holding = Portfolio(
                symbol=symbol,
                quantity=float(quantity),
                purchase_price=float(purchase_price)
            )
            db.session.add(holding)
            db.session.commit()
            return jsonify(holding.to_dict()), 201
        except (ValueError, TypeError):
            return jsonify({"error": "Cantidad y precio deben ser números válidos."}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error de base de datos: {e}"}), 500


@api_bp.route("/portfolio/<int:holding_id>", methods=["DELETE"])
def delete_from_portfolio(holding_id):
    """Elimina una acción del portafolio por su ID."""
    with current_app.app_context():
        holding = db.session.get(Portfolio, holding_id)
        if not holding:
            return jsonify({"error": "Registro no encontrado."}), 404

        db.session.delete(holding)
        db.session.commit()
        return '', 204

@api_bp.route("/dashboard/chart-data", methods=["GET"])
def get_dashboard_chart_data():
    """
    Devuelve datos históricos para las acciones y la métrica especificadas.
    Parámetros:
    - stock: uno o más símbolos de acciones (ej: ?stock=COPEC&stock=FALABELLA)
    - metric: la métrica a graficar (ej: ?metric=price)
    - days: número de días de historial a devolver (ej: ?days=30)
    """
    with current_app.app_context():
        stock_symbols = request.args.getlist("stock")
        metric = request.args.get("metric", "price")
        days_history = request.args.get("days", 30, type=int)
        
        if not stock_symbols:
            return jsonify({"error": "Debe especificar al menos un símbolo de acción."}), 400

        valid_metrics = {
            "price": FilteredStockHistory.price,
            "price_difference": FilteredStockHistory.price_difference,
            "percent_change": FilteredStockHistory.percent_change
        }

        if metric not in valid_metrics:
            return jsonify({"error": f"Métrica no válida. Válidas son: {list(valid_metrics.keys())}"}), 400

        metric_column = valid_metrics[metric]
        
        # Calcular la fecha de inicio para la consulta
        start_date = datetime.now(timezone.utc) - timedelta(days=days_history)
        # Consultar los datos
        history_data = db.session.query(
            FilteredStockHistory.symbol,
            FilteredStockHistory.timestamp,
            metric_column
        ).filter(
            FilteredStockHistory.symbol.in_(stock_symbols),
            FilteredStockHistory.timestamp >= start_date
        ).order_by(
            FilteredStockHistory.timestamp
        ).all()

        # Formatear los datos para Chart.js
        chart_data = {symbol: [] for symbol in stock_symbols}
        for symbol, timestamp, value in history_data:
            chart_data[symbol].append({
                "x": timestamp.isoformat(),
                "y": value
            })

        return jsonify(chart_data)