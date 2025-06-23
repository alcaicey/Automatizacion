# src/scripts/ai_financial_service.py
import os
import json
import logging
import time
from openai import OpenAI, RateLimitError
from src.models import PromptConfig
from src.extensions import db

logger = logging.getLogger(__name__)

# --- INICIO DE LA MODIFICACIÓN: Definir el esquema de la función ---
# Este esquema define la estructura del JSON que queremos recibir.
FINANCIAL_KPI_FUNCTION_SCHEMA = {
    "name": "get_financial_kpis_for_company",
    "description": "Extrae los indicadores financieros clave para una empresa chilena específica.",
    "parameters": {
        "type": "object",
        "properties": {
            "roe": {
                "type": "number",
                "description": "El Retorno sobre el Patrimonio (Return on Equity) en porcentaje. ej: 15.2"
            },
            "debt_to_equity": {
                "type": "number",
                "description": "El ratio Deuda/Patrimonio."
            },
            "beta": {
                "type": "number",
                "description": "El coeficiente Beta de la acción."
            },
            "analyst_recommendation": {
                "type": "string",
                "description": "El consenso de recomendación de analistas.",
                "enum": ["Comprar", "Mantener", "Vender", "N/A"]
            },
            "source": {
                "type": "string",
                "description": "La fuente principal de los datos (ej: 'Yahoo Finance')."
            }
        },
        "required": ["roe", "debt_to_equity", "beta", "analyst_recommendation", "source"]
    }
}
# --- FIN DE LA MODIFICACIÓN ---

def get_advanced_kpis(nemo: str, prompt_id: str = "openai_kpi_finance") -> dict | None:
    """
    Usa la API de OpenAI con Function Calling para obtener KPIs financieros.
    """
    prompt_config = db.session.get(PromptConfig, prompt_id)
    if not prompt_config:
        logger.error(f"No se encontró la configuración de prompt con ID: {prompt_id}")
        raise ValueError(f"Configuración de prompt '{prompt_id}' no encontrada.")

    client = OpenAI(api_key=prompt_config.api_key)
    prompt = prompt_config.prompt_template.format(nemo=nemo)

    try:
        logger.info(f"[AI Service] Solicitando KPIs para {nemo} con gpt-4o y Function Calling...")
        
        # --- INICIO DE LA MODIFICACIÓN: Nueva llamada a la API ---
        response = client.chat.completions.create(
            model=prompt_config.model_name, # Ahora usará "gpt-4o"
            messages=[
                {"role": "system", "content": "Eres un analista financiero experto."},
                {"role": "user", "content": f"Obtén los KPIs financieros para la empresa chilena con el nemotécnico {nemo}."}
            ],
            tools=[{"type": "function", "function": FINANCIAL_KPI_FUNCTION_SCHEMA}],
            tool_choice={"type": "function", "function": {"name": "get_financial_kpis_for_company"}} # Forzar el uso de la función
        )

        message = response.choices[0].message
        if not message.tool_calls:
            logger.warning(f"La IA no utilizó la función para {nemo}. Respuesta: {message.content}")
            return None

        # Extraemos los argumentos de la llamada a la función, que ya son un JSON
        function_args = json.loads(message.tool_calls[0].function.arguments)
        logger.info(f"[AI Service] Argumentos de función recibidos para {nemo}: {function_args}")
        # --- FIN DE LA MODIFICACIÓN ---

        # El resultado ya tiene la estructura correcta, solo validamos y devolvemos
        cleaned_data = {
            "roe": float(function_args.get("roe")) if function_args.get("roe") is not None else None,
            "debt_to_equity": float(function_args.get("debt_to_equity")) if function_args.get("debt_to_equity") is not None else None,
            "beta": float(function_args.get("beta")) if function_args.get("beta") is not None else None,
            "analyst_recommendation": str(function_args.get("analyst_recommendation", "N/A")),
            "source": str(function_args.get("source", "Desconocida"))
        }

        logger.info(f"[AI Service] Datos extraídos para {nemo}: {cleaned_data}")
        return cleaned_data

    except RateLimitError as e:
        # ... (el manejo de errores existente es correcto)
        error_info = e.response.json().get('error', {})
        # ...
    except Exception as e:
        logger.error(f"Error al procesar la solicitud de IA para {nemo}: {e}", exc_info=True)
        return None