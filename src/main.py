# src/main.py
import asyncio
import logging
import os
import signal
import sys
import atexit
import threading

from flask import Flask, send_from_directory, render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.extensions import db, socketio
from src.models import (
    User, StockPrice, Credential, LogEntry, ColumnPreference, StockFilter, 
    LastUpdate, Portfolio, Dividend, StockClosing, AdvancedKPI, KpiSelection, 
    PromptConfig, DividendColumnPreference, ClosingColumnPreference, KpiColumnPreference
)
from src.routes import register_blueprints
from src.utils.scheduler import stop_periodic_updates
from src.scripts.bot_page_manager import close_browser

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(name)s] %(asctime)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuración del bucle de eventos y el hilo del bot
LOOP = asyncio.new_event_loop()
BOT_THREAD = threading.Thread(target=LOOP.run_forever, daemon=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Creación de la aplicación Flask
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"), template_folder='templates')
app.config.update(
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=SQLALCHEMY_TRACK_MODIFICATIONS,
)
app.bot_event_loop = LOOP

# Inicialización de extensiones
CORS(app)
db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*", async_mode="gevent")

# Mapeo de modelos para el CRUD genérico
with app.app_context():
    app.model_map = {
        model.__tablename__: model 
        for model in db.Model.__subclasses__() 
        if hasattr(model, '__tablename__')
    }
    logger.info(f"Modelos mapeados para el CRUD: {list(app.model_map.keys())}")

# --- Definición de rutas de páginas HTML ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/historico")
def historico():
    return render_template("historico.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/logs")
def logs():
    return render_template("logs.html")

@app.route("/mantenedores")
def mantenedores():
    return render_template("mantenedores.html")

@app.route("/indicadores")
def indicadores():
    return render_template("indicadores.html")

@app.route("/login")
def login():
    return render_template("login.html")

# Llamada única para registrar todos los blueprints
register_blueprints(app)

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

# --- Funciones de ciclo de vida de la aplicación ---
def _cleanup_resources():
    logger.info("Iniciando cierre limpio de la aplicación...")
    stop_periodic_updates()
    if BOT_THREAD.is_alive():
        logger.info("Solicitando detención del bucle de eventos del bot...")
        try:
            future = asyncio.run_coroutine_threadsafe(close_browser(), LOOP)
            future.result(timeout=10)
        except Exception as e:
            logger.error(f"Error al cerrar navegador: {e}")
        finally:
            LOOP.call_soon_threadsafe(LOOP.stop)
            BOT_THREAD.join(timeout=5)
            if not BOT_THREAD.is_alive():
                logger.info("✓ Hilo del bot finalizado correctamente.")
    
atexit.register(_cleanup_resources)

def graceful_shutdown(signum, frame):
    logger.info(f"Recibida señal de apagado ({signum})...")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

def load_saved_credentials(app_context):
    with app_context:
        if not (os.getenv("BOLSA_USERNAME") and os.getenv("BOLSA_PASSWORD")):
            try:
                cred = Credential.query.first()
                if cred:
                    os.environ["BOLSA_USERNAME"] = cred.username
                    os.environ["BOLSA_PASSWORD"] = cred.password
                    logger.info("✓ Credenciales cargadas desde la base de datos.")
            except Exception as e:
                logger.error(f"No se pudieron cargar las credenciales desde la DB: {e}")

def start_bot_thread():
    if not BOT_THREAD.is_alive():
        logger.info("Iniciando hilo de fondo para el bot de Playwright...")
        BOT_THREAD.start()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_saved_credentials(app.app_context())

    start_bot_thread()

    # --- INICIO DE LA MODIFICACIÓN: Usar WSGIServer de Gevent explícitamente ---
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    logger.info("🚀 Iniciando servidor Flask con Gevent WSGIServer. La aplicación está lista en http://localhost:5000")
    
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 5000), 
        app, 
        handler_class=WebSocketHandler,
        log=logging.getLogger('geventwebsocket.handler') # Redirigir logs de gevent
    )
    server.serve_forever()
    # La línea socketio.run(...) ya no es necesaria y se ha eliminado.
    # --- FIN DE LA MODIFICACIÓN ---