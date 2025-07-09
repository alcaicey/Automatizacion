# src/routes/api/system_routes.py
import logging
from flask import Blueprint, jsonify, request, current_app

logger = logging.getLogger(__name__)
system_bp = Blueprint('system', __name__)

@system_bp.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ok"})

@system_bp.route('/version', methods=['GET'])
def get_version():
    return jsonify({"version": "1.0.0"})