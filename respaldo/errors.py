import logging
import traceback
from flask import Blueprint, jsonify, current_app, render_template
from src.models.log_entry import LogEntry
from src.extensions import db
from traceback import format_exc


errors_bp = Blueprint('errors', __name__)
logger = logging.getLogger(__name__)


# Manejador para errores de la aplicación (ej. 500 Internal Server Error)
@errors_bp.app_errorhandler(Exception)
def handle_unexpected_error(error):
    """
    Captura todas las excepciones no manejadas, las registra
    y devuelve una respuesta JSON genérica y estandarizada.
    """
    # Construir un mensaje de log detallado para el registro interno
    exception_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": format_exc()
    }
    
    # Loguear el error completo en el backend para un análisis posterior
    logger.critical(
        f"Error 500 no controlado: {exception_details['error_message']}", 
        extra=exception_details
    )

    # Devolver una respuesta segura y genérica al cliente
    response = {
        "error": "Error Interno del Servidor",
        "message": "Ocurrió un problema inesperado. El equipo de desarrollo ha sido notificado."
    }
    return jsonify(response), 500

# Manejador específico para errores 404 (No Encontrado)
@errors_bp.app_errorhandler(404)
def handle_not_found_error(error):
    """Maneja los errores 404 con una respuesta JSON."""
    return jsonify({
        "error": "Recurso No Encontrado",
        "message": "El endpoint o recurso solicitado no existe en el servidor."
    }), 404