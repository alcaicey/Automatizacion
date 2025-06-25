# src/routes/api/config_routes.py
import json
import logging
import os
from flask import jsonify, request, current_app

from src.routes.api import api_bp 
from src.extensions import db
from src.utils.db_io import get_latest_data
from src.models import (
    ColumnPreference, StockFilter, Credential, Dividend, DividendColumnPreference,
    StockClosing, ClosingColumnPreference, KpiColumnPreference
)

logger = logging.getLogger(__name__)

# ===================================================================
# ENDPOINTS DE CONFIGURACIÓN DE COLUMNAS
# ===================================================================

@api_bp.route("/columns", methods=["GET", "POST"])
def handle_columns():
    """Gestiona las preferencias de columnas para la tabla de Acciones."""
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

@api_bp.route("/dividends/columns", methods=["GET", "POST"])
def handle_dividend_columns():
    """Gestiona las preferencias de columnas para la tabla de Dividendos."""
    with current_app.app_context():
        if request.method == 'GET':
            all_cols = list(Dividend().to_dict().keys()) + ['is_ipsa']
            prefs = DividendColumnPreference.query.first()
            visible_cols = json.loads(prefs.columns_json) if prefs and prefs.columns_json else ['nemo', 'is_ipsa', 'fec_pago', 'fec_lim', 'val_acc', 'descrip_vc']
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data: return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(DividendColumnPreference, 1) or DividendColumnPreference(id=1)
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

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
                visible_cols = ['nemo', 'fec_fij_cie', 'precio_cierre_ant', 'monto_ant', 'un_transadas_ant', 'neg_ant', 'ren_actual', 'razon_pre_uti', 'PERTENECE_IPSA']
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data: return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(ClosingColumnPreference, 1) or ClosingColumnPreference(id=1)
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@api_bp.route("/kpis/columns", methods=["GET", "POST"])
def handle_kpi_columns():
    """Gestiona las preferencias de columnas para la tabla de KPIs."""
    with current_app.app_context():
        if request.method == 'GET':
            all_cols = [
                'nemo', 'precio_cierre_ant', 'razon_pre_uti', 'roe', 'dividend_yield', 
                'riesgo', 'beta', 'debt_to_equity', 'kpi_last_updated', 'kpi_source'
            ]
            prefs = KpiColumnPreference.query.first()
            if prefs and prefs.columns_json:
                visible_cols = json.loads(prefs.columns_json)
            else:
                visible_cols = ['nemo', 'precio_cierre_ant', 'razon_pre_uti', 'roe', 'dividend_yield', 'riesgo']
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data:
                return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(KpiColumnPreference, 1) or KpiColumnPreference(id=1)
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

# ===================================================================
# ENDPOINTS DE FILTROS Y CREDENCIALES
# ===================================================================

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