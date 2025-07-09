# FIX: Importar threading antes de monkey-patching para obtener hilos reales del S.O.
# Esto es crucial para ejecutar el bucle de eventos de asyncio (para Playwright)
# sin bloquear el bucle principal de eventlet.
import eventlet
eventlet.monkey_patch()

# src/main.py
import logging
import argparse

from src.app import create_app # Importar solo la factory
from src.extensions import socketio
from src.utils.logging_config import setup_logging
import src.prelaunch as prelaunch
from src.prelaunch import CriticalPrelaunchError

# Importar el paquete de modelos para que SQLAlchemy los descubra
import src.models

setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Función principal para configurar e iniciar la aplicación."""
    parser = argparse.ArgumentParser(description="Iniciar el servidor de la aplicación Flask.")
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help="Omitir las validaciones de pre-lanzamiento."
    )
    args = parser.parse_args()

    try:
        if not args.skip_checks:
            logger.info("🚀 Iniciando validaciones de pre-lanzamiento...")
            if not prelaunch.run_all_checks():
                raise CriticalPrelaunchError("Las comprobaciones de prelanzamiento fallaron. Saliendo.")
        else:
            logger.warning("Se han omitido las validaciones de pre-lanzamiento.")
        
        app = create_app()

        port = app.config.get('PORT', 5000)
        debug_mode = app.config.get('DEBUG', False)
        
        logger.info(f"✅ Servidor Flask iniciando en http://0.0.0.0:{port}")
        # Usar el socketio importado para correr la app.
        # Esto es crucial porque está configurado con el message_queue.
        socketio.run(app, host="0.0.0.0", port=port, debug=debug_mode)

    except CriticalPrelaunchError as e:
        logger.critical(f"Error crítico de prelanzamiento: {e}")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Servidor detenido por el usuario o el sistema.")
    finally:
        logger.info("Limpieza completada. Adiós.")

if __name__ == "__main__":
    main()