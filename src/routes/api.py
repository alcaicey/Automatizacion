from flask import Blueprint, jsonify, request, current_app, abort
from datetime import datetime

# Importar el servicio de bolsa
from src.scripts.bolsa_service import (
    get_latest_data,
    filter_stocks,
    run_bolsa_bot,
    start_periodic_updates,
    stop_periodic_updates,
    get_session_remaining_seconds,
)

from src.models.stock_price import StockPrice
from src.models import db

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
        # Iniciar la actualización en un hilo separado para no bloquear la
        # respuesta
        import threading
        app = current_app._get_current_object()
        update_thread = threading.Thread(target=run_bolsa_bot, kwargs={"app": app})
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
            app = current_app._get_current_object()
            start_periodic_updates(1, 3, app=app)
            return jsonify({
                "success": True,
                "message": (
                    "Actualizaciones automáticas configuradas (1-3 minutos)"
                ),
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })

        elif mode == "1-5":
            # Actualización cada 1-5 minutos
            app = current_app._get_current_object()
            start_periodic_updates(1, 5, app=app)
            return jsonify({
                "success": True,
                "message": (
                    "Actualizaciones automáticas configuradas (1-5 minutos)"
                ),
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


@api_bp.route('/session-time', methods=['GET'])
def session_time():
    """Devuelve el tiempo restante de la sesión, si está disponible."""
    try:
        remaining = get_session_remaining_seconds()
        return jsonify({
            "remaining_seconds": remaining,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }), 500


# ----- CRUD de precios almacenados -----

@api_bp.route('/prices', methods=['GET'])
def list_prices():
    """Devuelve una lista de precios almacenados."""
    try:
        limit = request.args.get('limit', type=int)
        query = StockPrice.query.order_by(StockPrice.timestamp.desc())
        if limit:
            query = query.limit(limit)
        prices = query.all()
        return jsonify([p.to_dict() for p in prices])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/prices', methods=['POST'])
def create_price():
    """Crea un nuevo registro de precio."""
    data = request.get_json() or {}
    try:
        ts = data.get('timestamp')
        ts = datetime.fromisoformat(ts) if ts else datetime.utcnow()
        price = StockPrice(
            symbol=data.get('symbol'),
            price=data.get('price', 0),
            variation=data.get('variation'),
            timestamp=ts,
        )
        db.session.add(price)
        db.session.commit()
        return jsonify(price.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route('/prices/<string:symbol>/<string:ts>', methods=['GET'])
def get_price(symbol, ts):
    """Obtiene un registro de precio por símbolo y timestamp."""
    try:
        timestamp = datetime.fromisoformat(ts)
    except ValueError:
        abort(400, description="Invalid timestamp format")
    price = StockPrice.query.filter_by(symbol=symbol, timestamp=timestamp).first_or_404()
    return jsonify(price.to_dict())


@api_bp.route('/prices/<string:symbol>/<string:ts>', methods=['PUT'])
def update_price(symbol, ts):
    """Actualiza un registro existente."""
    try:
        timestamp = datetime.fromisoformat(ts)
    except ValueError:
        abort(400, description="Invalid timestamp format")
    price = StockPrice.query.filter_by(symbol=symbol, timestamp=timestamp).first_or_404()
    data = request.get_json() or {}
    try:
        if 'symbol' in data:
            price.symbol = data['symbol']
        if 'price' in data:
            price.price = data['price']
        if 'variation' in data:
            price.variation = data['variation']
        if 'timestamp' in data:
            price.timestamp = datetime.fromisoformat(data['timestamp'])
        db.session.commit()
        return jsonify(price.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route('/prices/<string:symbol>/<string:ts>', methods=['DELETE'])
def delete_price(symbol, ts):
    """Elimina un registro de precio."""
    try:
        timestamp = datetime.fromisoformat(ts)
    except ValueError:
        abort(400, description="Invalid timestamp format")
    price = StockPrice.query.filter_by(symbol=symbol, timestamp=timestamp).first_or_404()
    try:
        db.session.delete(price)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
