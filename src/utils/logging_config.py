# src/utils/logging_config.py
import logging
import sys

def setup_logging():
    """
    Configura el sistema de logging para la aplicación.
    Establece un formato estándar y dirige los logs a la salida estándar,
    asegurando la compatibilidad con eventlet.
    """
    # force=True es crucial para asegurar que nuestra configuración se aplique
    # en entornos donde el logging ya pudo haber sido configurado (ej. pytest).
    # Omitir 'stream=sys.stdout' permite que eventlet parchee el handler por defecto.
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] [%(name)s] %(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )
    # Cambiamos el logger de 'module' a 'name' para tener más granularidad.
    logger = logging.getLogger(__name__)
    logger.info("Logging configurado.") 