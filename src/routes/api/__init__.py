# src/routes/api/__init__.py
from flask import Blueprint

# Importar los blueprints específicos de cada módulo de rutas
from .bot_routes import bot_bp
from .config_routes import config_bp
from .data_routes import data_bp
from .portfolio_routes import portfolio_bp
from .system_routes import system_bp
from .drainer_routes import drainer_bp

# 1. Creamos el blueprint principal para la API.
api_bp = Blueprint("api", __name__)

# 2. Registramos los blueprints "hijos" dentro del principal.
# Se estandarizan todos los prefijos para una API consistente
api_bp.register_blueprint(bot_bp, url_prefix='/bot')
api_bp.register_blueprint(config_bp, url_prefix='/config')
api_bp.register_blueprint(data_bp, url_prefix='/data')
api_bp.register_blueprint(portfolio_bp, url_prefix='/portfolio')
api_bp.register_blueprint(system_bp, url_prefix='/system')
api_bp.register_blueprint(drainer_bp, url_prefix='/drainer')