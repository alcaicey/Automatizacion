# src/scripts/ai_financial_service.py
import os
import json
import logging
import time
from openai import OpenAI
from src.models import PromptConfig
from src.extensions import db

logger = logging.getLogger(__name__)

def get_advanced_kpis(nemo: str, prompt_id: str = "openai_kpi_finance") -> dict | None:
    """
    Usa una configuración de prompt de la DB para obtener KPIs financieros.
    """
    # Obtener configuración desde la base de datos
    prompt_config = db.session.get(PromptConfig, prompt_id)
    if not prompt_config:
        logger.error(f"No se encontró la configuración de prompt con ID: {prompt_id}")
        raise ValueError(f"Configuración de prompt '{prompt_id}' no encontrada.")

    client = OpenAI(api_key=prompt_config.api_key)
    
    # Formatear el prompt con el nemotécnico
    prompt = prompt_config.prompt_template.format(nemo=nemo)

    try:
        logger.info(f"[AI Service] Solicitando KPIs para {nemo} a OpenAI...")
        response = client.chat.completions.create(
            model=prompt_config.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        logger.info(f"[AI Service] Respuesta recibida para {nemo}: {content}")
        data = json.loads(content)
        return data
    except Exception as e:
        logger.error(f"Error al procesar la solicitud de IA para {nemo}: {e}", exc_info=True)
        return None