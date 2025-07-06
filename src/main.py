# src/main.py

import asyncio
import logging
import threading
from flask import Flask, render_template
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

from src import config
from src.extensions import db, socketio
from src.routes.errors import errors_bp
from src.routes.user import user_bp
from src.routes.api import api_bp
from src.routes.crud_api import crud_bp
from src.routes.architecture import architecture_bp

# Importar todos los modelos para que SQLAlchemy los reconozca
from src.models import *

# Configuración inicial del logger
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] [%(name)s] %(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def create_app(config_module=config):
    """Crea y configura la aplicación Flask, sin inicializar extensiones."""
    app = Flask(__name__)
    app.config.from_object(config_module)
    return app

def main():
    app = create_app()

    # La inicialización de extensiones se hace aquí, en el scope principal.
    db.init_app(app)
    socketio.init_app(app, async_mode='gevent', cors_allowed_origins="*")

    # Configuración del logging a nivel de aplicación
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Iniciar el loop de eventos del bot explícitamente en un hilo de fondo
    def run_bot_loop(loop):
        asyncio.set_event_loop(loop)
        try:
            logger.info("Iniciando el event loop del bot en un hilo de fondo...")
            loop.run_forever()
        finally:
            if loop.is_running():
                loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            logger.info("El event loop del bot se ha detenido y cerrado.")

    bot_loop = asyncio.new_event_loop()
    app.bot_event_loop = bot_loop
    
    bot_thread = threading.Thread(target=run_bot_loop, args=(bot_loop,), daemon=True)
    bot_thread.start()
    logger.info("Hilo del bot de Playwright iniciado.")

    with app.app_context():
        db.create_all()
        # Lógica para registrar los modelos para el CRUD genérico
        app.model_map = {}
        for model in db.Model.__subclasses__():
            if hasattr(model, '__tablename__'):
                app.model_map[model.__tablename__] = model
        logger.info(f"Modelos mapeados para el CRUD: {list(app.model_map.keys())}")


    # Registrar las rutas de las páginas
    @app.route('/')
    def index(): return render_template('dashboard.html')
    @app.route('/dashboard')
    def dashboard(): return render_template('dashboard.html')
    @app.route('/historico')
    def historico(): return render_template('historico.html')
    @app.route('/indicadores')
    def indicadores(): return render_template('indicadores.html')
    @app.route('/logs')
    def logs(): return render_template('logs.html')
    @app.route('/mantenedores')
    def mantenedores(): return render_template('mantenedores.html')
    @app.route('/login')
    def login(): return render_template('login.html')

    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.svg')

    # Registrar Blueprints
    app.register_blueprint(errors_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(crud_bp, url_prefix='/api/crud')
    app.register_blueprint(architecture_bp)

    port = app.config.get('PORT', 5000)
    logger.info(f"🚀 Iniciando servidor Flask con Gevent WSGIServer. La aplicación está lista en http://localhost:{port}")
    http_server = WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
    
    try:
        http_server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Servidor detenido por el usuario o el sistema.")
    finally:
        logger.info("Iniciando limpieza de recursos...")
        if bot_loop.is_running():
            logger.info("Deteniendo el event loop del bot...")
            bot_loop.call_soon_threadsafe(bot_loop.stop)
        
        bot_thread.join(timeout=5)
        logger.info("Limpieza completada. Adiós.")

if __name__ == '__main__':
    main()