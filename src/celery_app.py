from celery import Celery
from src.config import REDIS_URL

# Crear la instancia de Celery aquí, de forma global
celery = Celery(
    __name__,
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tasks']
)

def init_celery(app):
    """
    Vincula la configuración de la app Flask con la instancia de Celery
    y establece el contexto de la aplicación para las tareas.
    """
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask 