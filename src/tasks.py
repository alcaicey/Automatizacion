# src/tasks.py
import logging
from src.celery_app import celery
from src.services.bolsa_service import run_bolsa_bot
from src.services.drainer_service import run_drainer_analysis

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def run_bolsa_bot_task(self):
    """
    Tarea de Celery que ejecuta el proceso principal de scraping del bot.
    """
    logger.info("Iniciando la tarea del bot de bolsa...")
    try:
        # Aquí irá la lógica de run_bolsa_bot
        run_bolsa_bot()
        logger.info("La tarea del bot de bolsa se completó con éxito.")
        return {'status': 'Completed'}
    except Exception as e:
        logger.error(f"Error en la tarea del bot de bolsa: {e}", exc_info=True)
        # Opcional: reintentar la tarea si falla
        # self.retry(exc=e, countdown=60)
        return {'status': 'Failed', 'error': str(e)}

@celery.task(bind=True, name='tasks.run_drainer_analysis')
def run_drainer_analysis_task(self):
    """Tarea Celery para ejecutar el análisis de eventos anómalos (drainer)."""
    logger.info(
        "Iniciando tarea de análisis de drainer.",
        extra={"task_id": self.request.id}
    )
    try:
        run_drainer_analysis()
        logger.info(
            "La tarea de análisis de drainer se completó con éxito.",
            extra={"task_id": self.request.id}
        )
        return {'status': 'Completed'}
    except Exception as e:
        logger.error(
            "Error en la tarea de análisis de drainer.",
            extra={"task_id": self.request.id, "error": str(e)},
            exc_info=True
        )
        return {'status': 'Failed', 'error': str(e)} 