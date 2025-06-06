import sys
import os
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

# Añadir el directorio raíz al path para importaciones absolutas
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importar blueprints
from src.routes.api import api_bp
from src.routes.user import user_bp

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Registrar blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')

# Ruta principal que sirve el frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Crear directorios necesarios si no existen
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"), exist_ok=True)
    
    # Iniciar la aplicación
    app.run(host='0.0.0.0', port=5000, debug=True)
