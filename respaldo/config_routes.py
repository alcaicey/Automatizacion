# src/routes/api/config_routes.py
import json
import logging
import os
from flask import jsonify, request, current_app, Blueprint
from sqlalchemy import select, delete

from src.extensions import db
from src.utils.db_io import get_latest_data
from src.models import (
    ColumnPreference, StockFilter, Credential, Dividend, DividendColumnPreference,
    StockClosing, ClosingColumnPreference, KpiColumnPreference, PortfolioColumnPreference,
    PromptConfig, KpiSelection, BotSetting
)

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)

# ===================================================================
# ENDPOINTS DE CONFIGURACIÓN DE COLUMNAS
# ===================================================================

@config_bp.route("/columns", methods=["GET", "POST"])
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
            prefs = db.session.get(ColumnPreference, 1) or ColumnPreference(id=1) # type: ignore
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@config_bp.route("/dividends/columns", methods=["GET", "POST"])
def handle_dividend_columns():
    """Gestiona las preferencias de columnas para la tabla de Dividendos."""
    with current_app.app_context():
        if request.method == 'GET':
            all_cols = list(Dividend().to_dict().keys()) + ['is_ipsa']
            prefs = DividendColumnPreference.query.first()
            visible_cols = json.loads(prefs.columns_json) if prefs and prefs.columns_json else ['nemo', 'is_ipsa', 'fec_pago', 'fec_lim', 'val_acc', 'descrip_vc', 'pre_ex_vc']
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data: return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(DividendColumnPreference, 1) or DividendColumnPreference(id=1) # type: ignore
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@config_bp.route("/closing/columns", methods=["GET", "POST"])
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
            prefs = db.session.get(ClosingColumnPreference, 1) or ClosingColumnPreference(id=1) # type: ignore
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@config_bp.route("/kpis/columns", methods=["GET", "POST"])
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
                visible_cols = ['nemo', 'precio_cierre_ant', 'razon_pre_uti', 'roe', 'dividend_yield', 'riesgo', 'kpi_last_updated', 'kpi_source']
            return jsonify({'all_columns': all_cols, 'visible_columns': visible_cols})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'columns' not in data:
                return jsonify({'error': 'Falta la lista de columnas'}), 400
            prefs = db.session.get(KpiColumnPreference, 1) or KpiColumnPreference(id=1) # type: ignore
            prefs.columns_json = json.dumps(data['columns'])
            db.session.add(prefs)
            db.session.commit()
            return jsonify({'success': True})

@config_bp.route("/kpi-prompt", methods=["GET", "POST"])
def handle_kpi_prompt():
    """Gestiona el prompt utilizado para la generación de KPIs por IA."""
    PROMPT_ID = "openai_kpi_finance"
    with current_app.app_context():
        if request.method == 'GET':
            prompt_config = db.session.get(PromptConfig, PROMPT_ID)
            # Devolver un prompt por defecto si no hay ninguno en la BD
            if not prompt_config:
                default_prompt = (
                    "Para la acción {nemo} con los siguientes datos de cierre:\n"
                    "```json\n{closing_data}\n```\n\n"
                    "Por favor, proporciona la siguiente información en formato JSON. No incluyas explicaciones adicionales fuera del JSON.\n"
                    "El JSON debe tener la siguiente estructura:\n"
                    "{\n"
                    "  \"kpis\": {\n"
                    "    \"roe\": <valor_numerico>,\n"
                    "    \"beta\": <valor_numerico>,\n"
                    "    \"debt_to_equity\": <valor_numerico>\n"
                    "  },\n"
                    "  \"analyst_recommendation\": \"<Comprar/Mantener/Vender>\",\n"
                    "  \"main_source\": \"<URL o nombre de la fuente principal>\",\n"
                    "  \"details\": {\n"
                    "    \"roe\": {\"source\": \"<URL/Fuente específica para ROE>\", \"calculation\": \"<Explicación de cómo se obtuvo el ROE>\"},\n"
                    "    \"beta\": {\"source\": \"<URL/Fuente específica para Beta>\", \"calculation\": \"<Explicación de cómo se obtuvo Beta>\"},\n"
                    "    \"debt_to_equity\": {\"source\": \"<URL/Fuente específica para Deuda/Patrimonio>\", \"calculation\": \"<Explicación de cómo se obtuvo>\"},\n"
                    "    \"analyst_recommendation\": {\"source\": \"<URL/Fuente del consenso>\", \"calculation\": \"<Metodología del consenso>\"}\n"
                    "  }\n"
                    "}"
                )
                return jsonify({'prompt': default_prompt})
            return jsonify({'prompt': prompt_config.prompt_template})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'prompt' not in data:
                return jsonify({'error': 'Falta el texto del prompt'}), 400
            
            prompt_config = db.session.get(PromptConfig, PROMPT_ID)
            if not prompt_config:
                return jsonify({
                    'error': 'La configuración de prompt no existe en la base de datos. '
                             'Debe ser creada primero a través del script de inicialización.'
                }), 404
            
            prompt_config.prompt_template = data['prompt']
            db.session.add(prompt_config)
            db.session.commit()
            return jsonify({'success': True})

# ===================================================================
# ENDPOINTS DE FILTROS Y CREDENCIALES
# ===================================================================

@config_bp.route("/filters", methods=["GET", "POST"])
def handle_filters():
    with current_app.app_context():
        if request.method == 'GET':
            stock_filter = StockFilter.query.first()
            codes = json.loads(stock_filter.codes_json) if stock_filter and stock_filter.codes_json else []
            return jsonify({'codes': codes, 'all': getattr(stock_filter, 'all', True)})
        
        if request.method == 'POST':
            data = request.get_json()
            if not data: return jsonify({'error': 'No se recibieron datos'}), 400
            stock_filter = db.session.get(StockFilter, 1) or StockFilter(id=1) # type: ignore
            stock_filter.codes_json = json.dumps(data.get('codes', []))
            stock_filter.all = data.get('all', False)
            db.session.add(stock_filter)
            db.session.commit()
            return jsonify({'success': True})

@config_bp.route('/credentials', methods=['POST'])
def update_credentials():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "message": "Datos incompletos."}), 400

    # Eliminar credenciales antiguas
    Credential.query.delete()

    # Guardar nuevas credenciales
    new_credential = Credential(username=data['username'], password=data['password'])
    db.session.add(new_credential)
    db.session.commit()

    return jsonify({"success": True, "message": "Credenciales guardadas con éxito."})

# --- Bot Settings ---
@config_bp.route('/bot_settings/<key>', methods=['GET'])
def get_bot_setting(key):
    """Obtiene una configuración específica del bot por su clave."""
    setting = BotSetting.query.filter_by(key=key).first()
    if setting:
        return jsonify({'key': setting.key, 'value': setting.value})
    # Devolver un 404 con un error claro si no se encuentra
    return jsonify({'error': 'Setting not found'}), 404

@config_bp.route('/bot_settings', methods=['POST'])
def update_bot_setting():
    """Crea o actualiza una configuración del bot."""
    data = request.get_json()
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({'error': 'Invalid data. "key" and "value" are required.'}), 400

    key = data['key']
    # Nos aseguramos de que el valor siempre sea una cadena
    value = str(data['value'])

    setting = BotSetting.query.filter_by(key=key).first()
    if setting:
        # Si existe, actualizamos su valor
        setting.value = value
    else:
        # Si no existe, creamos una nueva entrada
        setting = BotSetting(key=key, value=value)
        db.session.add(setting)
    
    try:
        db.session.commit()
        return jsonify({'key': setting.key, 'value': setting.value}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al guardar la configuración del bot: {e}")
        return jsonify({'error': 'Error al guardar en la base de datos'}), 500