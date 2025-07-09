# src/routes/api/data_routes.py
import logging
from flask import Blueprint, jsonify
from src.utils.db_io import get_latest_data
from src.utils.history_view import load_history

# 1. Crea un Blueprint específico para este módulo
data_bp = Blueprint('data_bp', __name__)

logger = logging.getLogger(__name__)

# 2. Usa ESE blueprint para decorar las rutas
@data_bp.route('/latest', methods=['GET'])
def get_stock_data_route():
    """Devuelve los datos de precios más recientes."""
    try:
        data = get_latest_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching latest stock data: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch stock data"}), 500

@data_bp.route('/history', methods=['GET'])
def get_stock_history_route():
    """Devuelve un resumen del historial de cargas."""
    try:
        history = load_history()
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch history"}), 500

@data_bp.route('/alerts', methods=['GET'])
def get_alerts():
    # Placeholder
    return jsonify([])

@data_bp.route('/news', methods=['GET'])
def get_news():
    # Placeholder
    return jsonify([])