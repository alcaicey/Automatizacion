import logging
import os
from datetime import datetime

from src.config import LOGS_DIR, USERNAME, PASSWORD

# Timestamp global para todos los logs de esta ejecución
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(LOGS_DIR, f"bolsa_bot_log_{timestamp}.txt")

# Logger base (puede usarse si se requiere global)
logger = logging.getLogger("bolsa_bot")
logger.setLevel(logging.INFO)

# Asegura que no se dupliquen handlers
if not logger.handlers:
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
    logger.addHandler(fh)

def validate_credentials() -> None:
    """Valida que existan las credenciales necesarias en variables de entorno."""
    global USERNAME, PASSWORD
    USERNAME = os.environ.get("BOLSA_USERNAME", USERNAME)
    PASSWORD = os.environ.get("BOLSA_PASSWORD", PASSWORD)
    if not USERNAME or not PASSWORD:
        raise ValueError("Credenciales faltantes: BOLSA_USERNAME o BOLSA_PASSWORD")

def configure_run_specific_logging(logger_instance: logging.Logger | None = None) -> None:
    """
    Permite configurar logging en módulos individuales,
    asegurando que compartan el archivo de log central.
    """
    if logger_instance and not logger_instance.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
        logger_instance.addHandler(fh)

__all__ = ["validate_credentials", "configure_run_specific_logging", "logger", "timestamp", "log_file"]