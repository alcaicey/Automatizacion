# ingresar_prompt_config.py
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.extensions import db
from src.models import PromptConfig

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)

# --- CONFIGURACIÓN INICIAL ---
PROMPT_ID = "openai_kpi_finance"
API_KEY = os.getenv("OPENAI_API_KEY", "TU_NUEVA_API_KEY_AQUI")
PROMPT_TEMPLATE = """
Eres un analista financiero experto en el mercado chileno. Tu tarea es encontrar y devolver únicamente un objeto JSON con los siguientes indicadores para la empresa chilena con el nemotécnico "{nemo}". Busca la información más reciente disponible en fuentes públicas como reportes financieros oficiales o portales de confianza (Yahoo Finance, Investing.com, etc.). Si un dato no está disponible, devuelve null para ese campo.

El JSON debe tener esta estructura exacta:
{{
  "roe": <valor numérico del Return on Equity en porcentaje, ej: 15.2>,
  "debt_to_equity": <valor numérico del ratio Deuda/Patrimonio>,
  "beta": <valor numérico del coeficiente Beta>,
  "analyst_recommendation": <string con el consenso de analistas: "Comprar", "Mantener", "Vender" o "N/A">
}}

Por favor, responde únicamente con el objeto JSON y nada más. Para el nemotécnico: "{nemo}"
"""

def add_prompt_to_db():
    with app.app_context():
        db.create_all()

        existing_prompt = db.session.get(PromptConfig, PROMPT_ID)
        if existing_prompt:
            print(f"Actualizando prompt existente con ID: {PROMPT_ID}")
            existing_prompt.api_key = API_KEY
            existing_prompt.prompt_template = PROMPT_TEMPLATE
        else:
            print(f"Creando nuevo prompt con ID: {PROMPT_ID}")
            new_prompt = PromptConfig(
                id=PROMPT_ID,
                api_provider="OpenAI",
                api_key=API_KEY,
                prompt_template=PROMPT_TEMPLATE
            )
            db.session.add(new_prompt)
        
        db.session.commit()
        print(f"✅ Configuración de prompt para '{PROMPT_ID}' guardada/actualizada en la base de datos.")

if __name__ == "__main__":
    if not API_KEY or "OPENAI_API_KEY" in API_KEY:
        print("❌ Por favor, añade tu OPENAI_API_KEY en el archivo .env o directamente en este script.")
    else:
        add_prompt_to_db()