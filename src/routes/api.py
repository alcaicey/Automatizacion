import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, current_app

# --- Lógica de Negocio y Utilidades ---
from src.scripts.bolsa_service import run_bolsa_bot
from src.utils.db_io import get_latest_data, filter_stocks, compare_last_two_db_entries
from src.utils.scheduler import start_periodic_updates, stop_periodic_updates
from ..utils import history_view

# --- Extensiones y Modelos ---
from src.extensions import db, socketio
from src.models import (
    Credential, LogEntry, ColumnPreference, StockFilter, StockPrice, Alert, 
    FilteredStockHistory, Portfolio, Dividend, DividendColumnPreference,
    StockClosing, ClosingColumnPreference # <-- AÑADIDO
)

# --- Lógica de Playwright y Servicios Específicos ---
from src.scripts import dividend_service, closing_service # <-- AÑADIDO
from src.scripts.bot_page_manager import get_page

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)
_sync_bot_running_lock = threading.Lock()

# ===================================================================
# ENDPOINTS PRINCIPALES (BOT, ACCIONES, HISTORIAL)
# ===================================================================

@api_bp.route("/bot-status", methods=["GET"])
def bot_status():
    is_running = _sync_bot_running_lock.locked()
    return jsonify({"is_running": is_running})

@api_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    if not _sync_bot_running_lock.acquire(blocking=False):
        return jsonify({"success": False, "message": "Ya hay una actualización de acciones en curso."}), 409
    
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
            if _sync_bot_running_lock.locked():
                _sync_bot_running_lock.release()
            logger.info("[API] Lock de actualización de acciones liberado.")
    
    threading.Thread(target=target_func, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de acciones iniciado."}), 202

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

# ===================================================================
# ENDPOINTS PARA DIVIDENDOS
# ===================================================================

@api_bp.route("/dividends", methods=["GET"])
def get_dividends():
    with current_app.app_context():
        dividends = Dividend.query.order_by(Dividend.payment_date.asc()).all()
        return jsonify([d.to_dict() for d in dividends])

@api_bp.route("/dividends/update", methods=["POST"])
def update_dividends():
    app_instance = current_app._get_current_object()

    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            if not loop.is_running():
                raise RuntimeError("El loop de eventos del bot no está corriendo.")
            
            async def update_task():
                page = await get_page()
                with app.app_context():
                    return await dividend_service.compare_and_update_dividends(page)
            
            future = asyncio.run_coroutine_threadsafe(update_task(), loop)
            result = future.result(timeout=120)
        except Exception as e:
            logger.error(f"Error en el hilo de actualización de dividendos: {e}", exc_info=True)
            result = {"error": str(e)}
        finally:
            socketio.emit('dividend_update_complete', result)

    threading.Thread(target=task_in_thread, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de dividendos iniciado."}), 202

@api_bp.route("/dividends/columns", methods=["GET", "POST"])
def handle_dividend_columns():
    with current_app.app_context():
        if request.method == 'GET':
            all_cols = list(Dividend().to_dict().keys())
            prefs = DividendColumnPreference.query.first()
            visible_cols = json.loads(prefs.columns_json) if prefs and prefs.columns_json else ['nemo', 'fec_pago', 'fec_lim', 'val_acc', 'descrip_vc']
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data: return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(DividendColumnPreference, 1) or DividendColumnPreference(id=1)
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

# ===================================================================
# ENDPOINTS PARA CIERRE BURSÁTIL (NUEVA FUNCIONALIDAD)
# ===================================================================
@api_bp.route("/closing", methods=["GET"])
def get_closing_data():
    """Obtiene los datos del último día de cierre bursátil disponible."""
    with current_app.app_context():
        latest_date = db.session.query(db.func.max(StockClosing.date)).scalar()
        if not latest_date:
            return jsonify([])
        
        closings = StockClosing.query.filter_by(date=latest_date).all()
        return jsonify([c.to_dict() for c in closings])

@api_bp.route("/closing/update", methods=["POST"])
def update_closing_data():
    """Inicia un hilo para actualizar los datos de Cierre Bursátil."""
    app_instance = current_app._get_current_object()

    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            if not loop.is_running(): raise RuntimeError("El loop de eventos del bot no está corriendo.")
            
            async def update_task():
                page = await get_page()
                with app.app_context():
                    return await closing_service.update_stock_closings(page)
            
            future = asyncio.run_coroutine_threadsafe(update_task(), loop)
            result = future.result(timeout=120)
        except Exception as e:
            logger.error(f"Error en el hilo de actualización de Cierre Bursátil: {e}", exc_info=True)
            result = {"error": str(e)}
        finally:
            socketio.emit('closing_update_complete', result)

    threading.Thread(target=task_in_thread, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de Cierre Bursátil iniciado."}), 202


# ===================================================================
# ENDPOINTS DE CONFIGURACIÓN (COLUMNAS, FILTROS, CREDENCIALES)
# ===================================================================

@api_bp.route("/columns", methods=["GET", "POST"])
def handle_columns():
    with current_app.app_context():
        if request.method == 'GET':
            latest_data = get_latest_data()
            all_cols = list(latest_data['data'][0].keys()) if latest_data.get('data') else ['NEMO', 'PRECIO_CIERRE', 'VARIACION']
            prefs = ColumnPreference.query.first()
            visible_cols = json.loads(prefs.columns_json) if prefs and prefs.columns_json else [col for col in ['NEMO', 'PRECIO_CIERRE', 'VARIACION'] if col in all_cols]
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data: return jsonify({'error': 'Falta la lista de columnas'}), 400
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
            codes = json.loads(stock_filter.codes_json) if stock_filter and stock_filter.codes_json else []
            return jsonify({'codes': codes, 'all': getattr(stock_filter, 'all', True)})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data: return jsonify({'error': 'No se recibieron datos'}), 400
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
        
        if request.method == 'POST':
            data = request.get_json() or {}
            username, password = data.get("username"), data.get("password")
            if not username or not password: return jsonify({"error": "Faltan credenciales."}), 400
            
            os.environ["BOLSA_USERNAME"], os.environ["BOLSA_PASSWORD"] = username, password
            
            if bool(data.get("remember")):
                cred = db.session.get(Credential, 1) or Credential(id=1)
                cred.username, cred.password = username, password
                db.session.add(cred)
            else:
                Credential.query.delete()
            
            db.session.commit()
            return jsonify({"success": True})

# ===================================================================
# ENDPOINTS DE PORTAFOLIO Y DASHBOARD
# ===================================================================

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

@api_bp.route("/dashboard/chart-data", methods=["GET"])
def get_dashboard_chart_data():
    with current_app.app_context():
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

# ===================================================================
# ENDPOINTS DE LOGS Y ALERTAS
# ===================================================================

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

@api_bp.route("/closing/columns", methods=["GET", "POST"])
def handle_closing_columns():
    """Gestiona las preferencias de columnas para la tabla de Cierre Bursátil."""
    with current_app.app_context():
        if request.method == 'GET':
            all_cols = list(StockClosing().to_dict().keys())
            
            prefs = ClosingColumnPreference.query.first()
            if prefs and prefs.columns_json:
                visible_cols = json.loads(prefs.columns_json)
            else:
                # Columnas visibles por defecto
                visible_cols = ['nemo', 'fec_fij_cie', 'precio_cierre_ant', 'monto_ant', 'un_transadas_ant', 'neg_ant', 'ren_actual', 'razon_pre_uti', 'PERTENECE_IPSA']
            
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data:
                return jsonify({'error': 'Falta la lista de columnas'}), 400
            
            prefs = db.session.get(ClosingColumnPreference, 1) or ClosingColumnPreference(id=1)
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})