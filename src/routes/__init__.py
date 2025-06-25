# src/routes/__init__.py

from .api import api_bp
from .architecture import architecture_bp
from .errors import errors_bp

def register_blueprints(app):
    """Registra todos los blueprints de la aplicación."""
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(errors_bp)
    app.register_blueprint(architecture_bp)