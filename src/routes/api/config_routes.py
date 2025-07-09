# src/routes/api/config_routes.py
import logging
from flask import Blueprint, jsonify, request
from src.extensions import db
from src.models import BotSetting

# 1. Crea un Blueprint específico para este módulo
config_bp = Blueprint('config_bp', __name__)

logger = logging.getLogger(__name__)

# 2. Usa ESE blueprint para decorar las rutas
@config_bp.route('/bot_settings/<key>', methods=['GET'])
def get_bot_setting(key):
    """Obtiene una configuración específica del bot por su clave."""
    try:
        logger.info(f"Buscando configuración con clave: {key}")
        setting = BotSetting.query.filter_by(key=key).first()
        
        if setting:
            logger.info(f"Configuración encontrada: {key} = {setting.value}")
            return jsonify({'key': setting.key, 'value': setting.value})
        else:
            logger.warning(f"No se encontró configuración para la clave: {key}. Devolviendo 404.")
            return jsonify({'error': 'Setting not found'}), 404
    except Exception as e:
        logger.error(f"Error en la base de datos al buscar la clave {key}: {e}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500


@config_bp.route('/bot_settings', methods=['POST'])
def update_bot_setting():
    """Crea o actualiza una configuración del bot."""
    data = request.get_json()
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({'error': 'Datos inválidos. Se requieren "key" y "value".'}), 400

    key = data['key']
    value = str(data['value']) # Asegurarse de que el valor sea una cadena

    try:
        setting = BotSetting.query.filter_by(key=key).first()

        if setting:
            logger.info(f"Actualizando configuración existente: {key} de '{setting.value}' a '{value}'")
            setting.value = value
        else:
            logger.info(f"Creando nueva configuración: {key} = {value}")
            setting = BotSetting()
            setting.key = key
            setting.value = value
            db.session.add(setting)
        
        db.session.commit()
        logger.info(f"Configuración para {key} guardada exitosamente.")
        
        return jsonify({'key': setting.key, 'value': setting.value}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error de base de datos al guardar la configuración {key}: {e}", exc_info=True)
        return jsonify({'error': 'Error interno al guardar en la base de datos'}), 500

@config_bp.route('/bot_settings', methods=['GET'])
def get_all_bot_settings():
    """Obtiene todas las configuraciones del bot."""
    try:
        settings = BotSetting.query.all()
        settings_data = [
            {
                "key": s.key,
                "value": s.value,
                "description": s.description,
                "last_modified": s.last_modified.isoformat()
            } for s in settings
        ]
        return jsonify(settings_data), 200
    except Exception as e:
        logger.error(f"Error getting all bot settings: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {e}"}), 500