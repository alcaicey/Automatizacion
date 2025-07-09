# src/utils/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configura el logging para que emita en formato JSON."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Prevenir que se añadan múltiples handlers si se llama varias veces
    if logger.hasHandlers():
        logger.handlers.clear()

    # Usar un handler que escriba a la salida estándar
    logHandler = logging.StreamHandler(sys.stdout)
    
    # Añadir campos estándar al log y permitir campos extra
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s',
        json_ensure_ascii=False
    )
    
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    logging.info("Logging estructurado (JSON) configurado.") 