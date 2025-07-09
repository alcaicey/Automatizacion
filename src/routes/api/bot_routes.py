# src/routes/api/bot_routes.py
import logging
import subprocess
import sys
import threading
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

# Crea un Blueprint específico para este módulo.
bot_bp = Blueprint('bot_bp', __name__)

# Lock para evitar (en la medida de lo posible) múltiples lanzamientos simultáneos.
_bot_process_lock = threading.Lock()

def _start_bot_process():
    """
    Función interna que contiene la lógica para iniciar el bot.
    Puede ser llamada desde la ruta HTTP o desde el manejador de Socket.IO.
    Devuelve True si se inició, False si ya estaba en ejecución o si hubo un error.
    """
    if not _bot_process_lock.acquire(blocking=False):
        logger.warning("Se intentó iniciar el bot, pero ya había un proceso en curso.")
        return False

    try:
        python_executable = sys.executable
        bot_script_path = "run_bot_process.py"
        command = [python_executable, bot_script_path]
        
        logger.info(f"Lanzando subproceso con el comando: {' '.join(command)}")
        subprocess.Popen(command)

        # Liberar el lock después de un tiempo para permitir futuros lanzamientos.
        threading.Timer(300.0, _bot_process_lock.release).start() # 5 minutos
        return True

    except Exception as e:
        logger.critical(f"No se pudo iniciar el subproceso del bot: {e}", exc_info=True)
        if _bot_process_lock.locked():
            _bot_process_lock.release()
        return False

@bot_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    """
    Endpoint HTTP para iniciar el proceso de scraping del bot.
    """
    logger.info("Solicitud HTTP recibida en /api/bot/stocks/update")
    success = _start_bot_process()
    if success:
        return jsonify({"status": "started", "message": "El proceso de actualización del bot ha sido iniciado."}), 202
    else:
        return jsonify({"status": "already_running", "message": "Ya hay una actualización de acciones en curso."}), 409