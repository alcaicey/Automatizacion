# ingresar_prompt_config.py
import os
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Importar todo lo necesario ---
from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.extensions import db
from src.models import PromptConfig

# Configuración mínima de la app Flask para acceder a la DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)

# --- CONFIGURACIÓN INICIAL ---
# Identificador único para esta configuración de prompt
PROMPT_ID = "openai_kpi_finance"

# Tu clave de API de OpenAI (leída desde el entorno)
API_KEY = os.getenv("OPENAI_API_KEY", "TU_API_KEY_AQUI_SI_NO_ESTA_EN_ENV")

# El nuevo prompt, más simple, para usar con Function Calling
PROMPT_TEMPLATE = """
Eres un analista financiero experto en el mercado chileno. Tu tarea es obtener los indicadores clave de rendimiento (KPIs) más recientes para la empresa con el nemotécnico "{nemo}". Utiliza fuentes públicas y fiables como la Bolsa de Santiago, Yahoo Finance, Investing.com o los reportes de la CMF.
"""

# El nuevo modelo recomendado por OpenAI
MODEL_NAME = "gpt-4o"

def add_prompt_to_db():
    """
    Inserta o actualiza la configuración del prompt en la base de datos.
    Esto asegura que la aplicación siempre use la última versión del prompt y modelo.
    """
    with app.app_context():
        # Asegurarse de que la tabla exista
        db.create_all()

        # Buscar si ya existe una configuración con este ID
        existing_prompt = db.session.get(PromptConfig, PROMPT_ID)
        
        if existing_prompt:
            print(f"Actualizando prompt existente con ID: {PROMPT_ID}")
            existing_prompt.api_key = API_KEY
            existing_prompt.prompt_template = PROMPT_TEMPLATE
            existing_prompt.model_name = MODEL_NAME
        else:
            print(f"Creando nuevo prompt con ID: {PROMPT_ID}")
            new_prompt = PromptConfig(
                id=PROMPT_ID,
                api_provider="OpenAI",
                api_key=API_KEY,
                prompt_template=PROMPT_TEMPLATE,
                model_name=MODEL_NAME
            )
            db.session.add(new_prompt)
        
        # Guardar los cambios en la base de datos
        db.session.commit()
        print(f"✅ Configuración de prompt para '{PROMPT_ID}' guardada/actualizada en la base de datos.")
        print(f"   - Modelo a usar: {MODEL_NAME}")

if __name__ == "__main__":
    if not API_KEY or "TU_API_KEY_AQUI" in API_KEY:
        print("❌ ADVERTENCIA: No se encontró una API Key válida en las variables de entorno (OPENAI_API_KEY).")
        print("   Por favor, añade tu clave al archivo .env o directamente en este script antes de continuar.")
    else:
        add_prompt_to_db()