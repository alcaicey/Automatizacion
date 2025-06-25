# src/routes/__init__.py

from .api import api_bp
from .architecture import architecture_bp
from .errors import errors_bp
# Ya no necesitamos importar user_bp y crud_bp aquí

def register_blueprints(app):
    """Registra todos los blueprints de la aplicación."""
    # Registramos el blueprint principal de la API
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Registramos los otros blueprints a nivel de la app
    app.register_blueprint(errors_bp)
    app.register_blueprint(architecture_bp)

    # Las siguientes líneas ya no son necesarias porque se manejan dentro de api/__init__.py
    # app.register_blueprint(user_bp, url_prefix="/api")
    # app.register_blueprint(crud_bp, url_prefix="/api")