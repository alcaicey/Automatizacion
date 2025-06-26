# src/routes/api/__init__.py

from flask import Blueprint

# Importamos los otros blueprints que irán bajo /api
from ..user import user_bp
from ..crud_api import crud_bp

# 1. Creamos el blueprint principal para la API.
api_bp = Blueprint("api", __name__)

# 2. Registramos los blueprints "hijos" dentro del principal.
#    Heredarán el prefijo de URL de `api_bp`.
api_bp.register_blueprint(user_bp)
api_bp.register_blueprint(crud_bp)

# 3. Importamos los módulos de rutas para que se registren en `api_bp`
from . import bot_routes
from . import data_routes
from . import config_routes
from . import portfolio_routes
from . import system_routes
from . import drainer_routes # <-- AÑADIR ESTA LÍNEA