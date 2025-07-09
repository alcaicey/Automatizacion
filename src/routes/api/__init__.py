# src/routes/api/__init__.py
from flask import Blueprint

# 1. Crear el Blueprint principal de la API
api_bp = Blueprint("api", __name__)

# 2. Importar los Blueprints específicos de cada módulo
from .bot_routes import bot_bp
from .config_routes import config_bp
from .data_routes import data_bp
from .portfolio_routes import portfolio_bp
from .system_routes import system_bp
from .drainer_routes import drainer_bp

# 3. Registrar cada Blueprint "hijo" en el "padre" con su prefijo
api_bp.register_blueprint(bot_bp, url_prefix='/bot')
api_bp.register_blueprint(config_bp, url_prefix='/config')
api_bp.register_blueprint(data_bp, url_prefix='/data')
api_bp.register_blueprint(portfolio_bp, url_prefix='/portfolio')
api_bp.register_blueprint(system_bp, url_prefix='/system')
api_bp.register_blueprint(drainer_bp, url_prefix='/drainer')

# 4. Importar los módulos al final para activar los decoradores de ruta
from . import bot_routes, config_routes, data_routes, drainer_routes, portfolio_routes, system_routes