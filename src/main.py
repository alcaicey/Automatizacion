import os
import sys

# Add project root to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

from src.extensions import socketio
from src.models import db
from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Importar blueprints
from src.routes.api import api_bp
from src.routes.user import user_bp

# Crear la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
CORS(app)  # Habilitar CORS para todas las rutas
db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

# Registrar blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')


# Preguntar por la configuración de ejecución interactiva del bot
def _prompt_non_interactive():
    """Solicita al usuario si desea activar el modo no interactivo."""
    if os.environ.get("BOLSA_NON_INTERACTIVE") is not None:
        return

    try:
        resp = input(
            "\u00bfEjecutar bolsa_santiago_bot.py sin confirmaci\u00f3n de usuario? "
            "[s/N]: "
        ).strip().lower()
    except EOFError:
        resp = ""

    if resp in {"s", "y", "yes", "si"}:
        os.environ["BOLSA_NON_INTERACTIVE"] = "1"
    else:
        os.environ["BOLSA_NON_INTERACTIVE"] = "0"

# Ruta principal que sirve el frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    # Crear directorios necesarios si no existen
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    # Configurar la variable BOLSA_NON_INTERACTIVE si es necesario
    _prompt_non_interactive()

    # Iniciar la aplicación con soporte WebSocket
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
