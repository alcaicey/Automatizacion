# src/main.py

# El monkey-patch sigue siendo lo primero para que SocketIO funcione.
import eventlet
eventlet.monkey_patch()

import logging
from src.app import create_app
from src.extensions import socketio
from src.utils.logging_config import setup_logging

# Importar modelos para que SQLAlchemy los descubra
import src.models

setup_logging()
logger = logging.getLogger(__name__)

# Crear la App Flask
app = create_app()

def main():
    """Punto de entrada principal que inicia la aplicación."""
    try:
        port = app.config.get('PORT', 5000)
        debug_mode = app.config.get('DEBUG', False)
        
        logger.info(f"✅ Servidor Flask + Socket.IO iniciando en http://0.0.0.0:{port}")
        
        # Simplemente corre el servidor. No más hilos ni loops de asyncio aquí.
        socketio.run(app, host="0.0.0.0", port=port, debug=debug_mode)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Servidor detenido.")
    finally:
        logger.info("Aplicación finalizada.")

if __name__ == "__main__":
    main()