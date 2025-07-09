# src/app.py
import logging
import asyncio
from flask import Flask, render_template, jsonify
import time

from src import config
from src.extensions import db, socketio
from src.celery_app import init_celery
from src.routes.errors import errors_bp
from src.routes.user import user_bp
from src.routes.api import api_bp
from src.routes.crud_api import crud_bp
from src.routes.architecture import architecture_bp

# Importar el paquete de modelos para que SQLAlchemy los descubra
import src.models

# Configuración inicial del logger para este módulo
logger = logging.getLogger(__name__)

# Variable global para el 'cache buster'
app_version = int(time.time())

def create_app(config_module=config):
    """
    Factory para crear y configurar la instancia de la aplicación Flask.
    """
    logger.info("[app.py] Iniciando create_app...")
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_module)
    logger.info("[app.py] Configuración cargada.")
    
    # Añadir 'version' al contexto de la plantilla para cache-busting
    @app.context_processor
    def inject_version():
        return dict(version=app_version)
        
    # Inicializar extensiones
    db.init_app(app)
    # Cambiar el async_mode a eventlet
    socketio.init_app(app, async_mode='eventlet', message_queue=app.config.get('REDIS_URL'))
    
    # --- AÑADIR ESTA LÍNEA ---
    # Importar los manejadores de eventos para registrarlos con la instancia de socketio
    from . import socket_events
    # ---------------------------

    logger.info("[app.py] Extensiones inicializadas.")

    # Inicializar Celery con la app
    init_celery(app)
    logger.info("[app.py] Celery inicializado y vinculado con la app.")

    with app.app_context():
        # Crear todas las tablas de la base de datos
        logger.info("[app.py] Creando tablas de la base de datos (si no existen)...")
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
    logger.info("[app.py] Blueprints registrados.")
    
    # --- AÑADIR ESTAS LÍNEAS PARA DEBUGGING ---
    if app.config.get('DEBUG'):
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.INFO)
    # -------------------------------------------

    # --- AÑADIR ESTE BLOQUE JUSTO ANTES DEL RETURN ---
    @app.errorhandler(404)
    def page_not_found(e):
        output = "Rutas disponibles en la aplicación:\n"
        rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
        for rule in rules:
            methods = ','.join(sorted(rule.methods))
            output += f"- Endpoint: {rule.endpoint}, Métodos: {methods}, Ruta: {rule.rule}\n"
        
        # Imprime la lista de rutas en la consola del servidor
        print(output) 
        
        # Devuelve la respuesta JSON estándar al navegador
        return jsonify(error=str(e)), 404
    # -------------------------------------------------

    logger.info("[app.py] Creación de la aplicación completada.")
    return app 