import os
from flask import Flask
from dotenv import load_dotenv

# --- INICIO DE LA CORRECCIÓN: Importar desde las fuentes correctas ---
from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.extensions import db
from src.models.credentials import Credential
# --- FIN DE LA CORRECCIÓN ---

# Cargar variables de entorno desde .env
load_dotenv()

# --- CONFIGURA TUS CREDENCIALES AQUÍ ---
BOLSA_USERNAME = os.getenv("BOLSA_USERNAME", "alcaicey@gmail.com")
BOLSA_PASSWORD = os.getenv("BOLSA_PASSWORD", "Carlosirenee13#")
# -----------------------------------------

# Configuración de la app Flask para acceder a la DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)

def add_credentials_to_db():
    with app.app_context():
        # Asegurarse de que las tablas existan
        db.create_all()

        # Borrar cualquier credencial existente para evitar duplicados
        Credential.query.delete()
        print("Credenciales antiguas eliminadas.")
        
        # Crear la nueva entrada
        new_cred = Credential(id=1, username=BOLSA_USERNAME, password=BOLSA_PASSWORD)
        db.session.add(new_cred)
        
        # Guardar los cambios
        db.session.commit()
        print(f"✅ Credenciales para el usuario '{BOLSA_USERNAME}' guardadas en la base de datos.")

if __name__ == "__main__":
    if BOLSA_USERNAME == "alcaicey@gmail.com" or BOLSA_PASSWORD == "Carlosirenee13#":
        print("Igresadas correctamente.")
    else:
        print("❌ Por favor, edita el script ingresar_credenciales.py y añade tus credenciales reales.")
        add_credentials_to_db()