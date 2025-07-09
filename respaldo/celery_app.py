from celery import Celery
from src import config

# Crear la instancia de Celery aquí, de forma global
celery = Celery(
    __name__,
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/0',
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