import os
import sys
import signal
import atexit
import asyncio

# Asegurar ruta raíz en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

from src.extensions import socketio
from src.models import db
from src.models.credentials import Credential
from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

# -------------------------------------------------------------------------
# Configuración inicial ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "src", "static"))
app.config.update(
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=SQLALCHEMY_TRACK_MODIFICATIONS,
)

CORS(app)

db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

# -------------------------------------------------------------------------
# Blueprints ---------------------------------------------------------------
from src.pages import pages_bp  # noqa: E402
from src.routes.api import api_bp  # noqa: E402
from src.routes.user import user_bp  # noqa: E402
from src.routes.errors import errors_bp  # noqa: E402
from src.routes.architecture import architecture_bp  # noqa: E402

app.register_blueprint(pages_bp)  # UI pages (/, /historico, …)
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(errors_bp, url_prefix="/api")
app.register_blueprint(architecture_bp)

# -------------------------------------------------------------------------
# Archivos estáticos extra
@app.route("/static/<path:path>")
def static_files(path):  # pylint: disable=unused-argument
    return send_from_directory(app.static_folder, path)

# -------------------------------------------------------------------------
# Limpieza y shutdown ------------------------------------------------------
def _cleanup_resources():
    """Libera hilos y Playwright al terminar."""
    try:
        from src.scripts.bolsa_service import stop_periodic_updates  # type: ignore
        stop_periodic_updates()
    except Exception:
        pass
    try:
        from src.scripts.bolsa_santiago_bot import close_playwright_resources  # type: ignore
        asyncio.run(close_playwright_resources())
    except Exception:
        pass

def graceful_shutdown(signum, frame):  # noqa: D401, pylint: disable=unused-argument
    _cleanup_resources()
    try:
        socketio.stop()
    except Exception:
        pass
    sys.exit(0)

after_signals = (signal.SIGINT, signal.SIGTERM)
atexit.register(_cleanup_resources)
for _sig in after_signals:
    signal.signal(_sig, graceful_shutdown)

# -------------------------------------------------------------------------
# Utilidades ---------------------------------------------------------------
def load_saved_credentials():
    cred = Credential.query.first()
    if cred:
        os.environ.setdefault("BOLSA_USERNAME", cred.username)
        os.environ.setdefault("BOLSA_PASSWORD", cred.password)

# -------------------------------------------------------------------------
# Entrada ------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    with app.app_context():
        db.create_all()
        load_saved_credentials()

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
