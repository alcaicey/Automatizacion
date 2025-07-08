# src/app.py
import logging
import asyncio
import threading
from flask import Flask, render_template

from src import config
from src.extensions import db, socketio
from src.routes.errors import errors_bp
from src.routes.user import user_bp
from src.routes.api import api_bp
from src.routes.crud_api import crud_bp
from src.routes.architecture import architecture_bp

# Importar el paquete de modelos para que SQLAlchemy los descubra
import src.models

logger = logging.getLogger(__name__)

def run_bot_loop(loop):
    """Función de destino para el hilo del bot, ejecuta el bucle de eventos."""
    logger.info("Iniciando el event loop del bot en un hilo de fondo...")
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    except Exception as e:
        logger.error(f"Error CRÍTICO en el event loop del bot: {e}", exc_info=True)
    finally:
        logger.info("Event loop del bot detenido.")

def create_app(config_module=config):
    """
    Factory para crear y configurar la instancia de la aplicación Flask.
    """
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_module)
    
    # Inicializar extensiones
    db.init_app(app)
    # Cambiar el async_mode a eventlet
    socketio.init_app(app, async_mode='eventlet')

    with app.app_context():
        # Crear todas las tablas de la base de datos
        db.create_all()
        # Lógica para registrar los modelos para el CRUD genérico
        model_map = {
            model.__tablename__: model for model in db.Model.__subclasses__() # type: ignore
            if hasattr(model, '__tablename__')
        }
        app.model_map = model_map # type: ignore
        logger.info(f"Modelos mapeados para el CRUD: {list(app.model_map.keys())}") # type: ignore

    # Registrar las rutas de las páginas
    @app.route('/')
    def index(): return render_template('dashboard.html', page_name='dashboard')
    @app.route('/dashboard')
    def dashboard(): return render_template('dashboard.html', page_name='dashboard')
    @app.route('/historico')
    def historico(): return render_template('historico.html', page_name='historico')
    @app.route('/indicadores')
    def indicadores(): return render_template('indicadores.html', page_name='indicadores')
    @app.route('/logs')
    def logs(): return render_template('logs.html', page_name='logs')
    @app.route('/mantenedores')
    def mantenedores(): return render_template('mantenedores.html', page_name='mantenedores')
    @app.route('/login')
    def login(): return render_template('login.html', page_name='login')

    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.svg')

    # Registrar Blueprints
    app.register_blueprint(errors_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(crud_bp, url_prefix='/api/crud')
    app.register_blueprint(architecture_bp)

    return app 