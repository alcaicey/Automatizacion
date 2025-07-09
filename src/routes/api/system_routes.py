# src/routes/api/system_routes.py
import logging
from flask import Blueprint, jsonify

# 1. Crea un Blueprint específico para este módulo
system_bp = Blueprint('system_bp', __name__)

logger = logging.getLogger(__name__)

# 2. Usa ESE blueprint para decorar las rutas
@system_bp.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ok"})

@system_bp.route('/version', methods=['GET'])
def get_version():
    return jsonify({"version": "1.0.0"})