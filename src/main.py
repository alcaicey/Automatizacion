# FIX: Importar threading antes de monkey-patching para obtener hilos reales del S.O.
# Esto es crucial para ejecutar el bucle de eventos de asyncio (para Playwright)
# sin bloquear el bucle principal de eventlet.
import threading
import eventlet

eventlet.monkey_patch()

# src/main.py
import logging
import argparse
import asyncio

from src.app import create_app, run_bot_loop
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

    app = None
    try:
        if not args.skip_checks:
            logger.info("🚀 Iniciando validaciones de pre-lanzamiento...")
            if not prelaunch.run_all_checks():
                raise CriticalPrelaunchError("Las comprobaciones de prelanzamiento fallaron. Saliendo.")
        else:
            logger.warning("Se han omitido las validaciones de pre-lanzamiento.")

        app = create_app()

        # Iniciar el bucle de eventos del bot en un hilo separado
        bot_event_loop = asyncio.new_event_loop()
        bot_thread = threading.Thread(
            target=run_bot_loop,
            args=(bot_event_loop,),
            daemon=True
        )
        # Comentado temporalmente para diagnosticar el bloqueo del servidor.
        # bot_thread.start()
        
        # Adjuntar el bucle y el hilo a la app para acceso global
        app.bot_event_loop = bot_event_loop # type: ignore
        app.bot_thread = bot_thread # type: ignore

        port = app.config.get('PORT', 5000)
        debug_mode = app.config.get('DEBUG', False)
        
        logger.info(f"✅ Servidor Flask iniciando en http://0.0.0.0:{port}")
        socketio.run(app, host="0.0.0.0", port=port, debug=debug_mode)

    except CriticalPrelaunchError as e:
        logger.critical(f"Error crítico de prelanzamiento: {e}")
        # El programa terminará aquí si las validaciones fallan.
    except (KeyboardInterrupt, SystemExit):
        logger.info("Servidor detenido por el usuario o el sistema.")
    finally:
        if app and hasattr(app, 'bot_event_loop'):
            loop = getattr(app, 'bot_event_loop', None)
            if loop and loop.is_running():
                logger.info("Deteniendo el event loop del bot...")
                loop.call_soon_threadsafe(loop.stop)
        
        if app and hasattr(app, 'bot_thread'):
            thread = getattr(app, 'bot_thread', None)
            if thread and thread.is_alive():
                logger.info("Esperando al hilo del bot...")
                thread.join(timeout=5)

        logger.info("Limpieza completada. Adiós.")

if __name__ == "__main__":
    main()