from flask import Blueprint, jsonify, request
import sys
import os
import json
from datetime import datetime

# Importar el servicio de bolsa
from src.scripts.bolsa_service import get_latest_data, filter_stocks, run_bolsa_bot, start_periodic_updates, stop_periodic_updates

# Crear el blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/stocks', methods=['GET'])
def get_stocks():
    """
    Endpoint para obtener todas las acciones o filtrar por códigos
    """
    try:
        # Obtener códigos de acciones de los parámetros de consulta
        stock_codes = request.args.getlist('code')
        
        if stock_codes:
            # Filtrar acciones por códigos
            result = filter_stocks(stock_codes)
        else:
            # Obtener todas las acciones
            result = get_latest_data()
            
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }), 500

@api_bp.route('/stocks/update', methods=['POST'])
def update_stocks():
    """
    Endpoint para actualizar manualmente los datos de acciones
    """
    try:
        # Iniciar la actualización en un hilo separado para no bloquear la respuesta
        import threading
        update_thread = threading.Thread(target=run_bolsa_bot)
        update_thread.daemon = True
        update_thread.start()
        
        return jsonify({
            "success": True,
            "message": "Proceso de actualización iniciado",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }), 500

@api_bp.route('/stocks/auto-update', methods=['POST'])
def set_auto_update():
    """
    Endpoint para configurar la actualización automática
    """
    try:
        data = request.get_json()
        
        if not data or "mode" not in data:
            return jsonify({
                "error": "Se requiere el parámetro 'mode'",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }), 400
        
        mode = data["mode"]
        
        if mode == "off":
            # Detener actualizaciones automáticas
            stop_periodic_updates()
            return jsonify({
                "success": True,
                "message": "Actualizaciones automáticas desactivadas",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
        
        elif mode == "1-3":
            # Actualización cada 1-3 minutos
            start_periodic_updates(1, 3)
            return jsonify({
                "success": True,
                "message": "Actualizaciones automáticas configuradas (1-3 minutos)",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
        
        elif mode == "1-5":
            # Actualización cada 1-5 minutos
            start_periodic_updates(1, 5)
            return jsonify({
                "success": True,
                "message": "Actualizaciones automáticas configuradas (1-5 minutos)",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
        
        else:
            return jsonify({
                "error": "Modo no válido. Opciones: 'off', '1-3', '1-5'",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }), 400
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }), 500
