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

from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.extensions import db, socketio
from src.models.credentials import Credential
from src.routes.api import api_bp
from src.routes.architecture import architecture_bp
from src.routes.errors import errors_bp
from src.routes.user import user_bp
from src.utils.scheduler import stop_periodic_updates
from src.scripts.bot_page_manager import close_browser

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(name)s] %(asctime)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

LOOP = asyncio.new_event_loop()
BOT_THREAD = threading.Thread(target=LOOP.run_forever, daemon=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"), template_folder='templates')
app.config.update(
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=SQLALCHEMY_TRACK_MODIFICATIONS,
)
app.bot_event_loop = LOOP

CORS(app)
db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/historico")
def historico():
    return render_template("historico.html")

@app.route("/logs")
def logs():
    return render_template("logs.html")

@app.route("/login")
def login():
    return render_template("login.html")

app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(errors_bp, url_prefix="/api")
app.register_blueprint(architecture_bp)

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

def _cleanup_resources():
    logger.info("Iniciando cierre limpio de la aplicación...")
    stop_periodic_updates()
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Detenemos el hilo y cerramos el navegador de forma más directa
    if BOT_THREAD.is_alive():
        logger.info("Solicitando detención del bucle de eventos del bot...")
        # Simplemente corremos la corutina de cierre.
        # No es necesario `run_coroutine_threadsafe` aquí.
        try:
            asyncio.run(close_browser())
        except RuntimeError:
            # Puede que el bucle ya esté cerrado, es seguro ignorarlo.
            pass
        
        LOOP.call_soon_threadsafe(LOOP.stop)
        BOT_THREAD.join(timeout=5)
        if not BOT_THREAD.is_alive():
            logger.info("✓ Hilo del bot finalizado correctamente.")
    # --- FIN DE LA CORRECCIÓN ---
    
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

    logger.info("🚀 Iniciando servidor Flask. La aplicación está lista en http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)