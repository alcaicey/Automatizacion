# src/scripts/ai_financial_service.py
import logging
import random
import asyncio
from datetime import datetime
from flask import current_app
from src.extensions import db
from src.models.advanced_kpi import AdvancedKPI

# Este es un archivo de stub/marcador de posición.
# En un futuro, aquí iría la lógica para conectarse a una API de IA
# (como OpenAI, Google Gemini, etc.) para obtener análisis financieros.

logger = logging.getLogger(__name__)

class AIFinancialService:
    def __init__(self, api_key: str):
        # En una implementación real, aquí se usaría la api_key
        if not api_key:
            logger.warning("[AI Service] La clave de API no fue proporcionada.")
        self.api_key = api_key

    async def calculate_and_store_single_kpi(self, nemo: str) -> dict | None:
        """
        Simula la obtención y almacenamiento de KPIs para un único símbolo de acción,
        interactuando directamente con la base de datos.
        """
        with current_app.app_context():
            logger.info(f"[AI Service] Solicitando y guardando KPI para '{nemo}' (simulado).")
            
            # Simula una llamada de red asíncrona
            await asyncio.sleep(random.uniform(1, 3))

            # Devolver None ocasionalmente para simular fallos de la IA
            if random.random() < 0.1:
                logger.warning(f"[AI Service] Simulación de fallo de IA para '{nemo}'.")
                return None

            recommendations = ["Comprar", "Mantener", "Vender"]
            riesgo = random.choice(recommendations)
            
            kpi_data = {
                'nemo': nemo,
                'roe': round(random.uniform(5.0, 25.0), 2),
                'beta': round(random.uniform(0.5, 1.8), 2),
                'debt_to_equity': round(random.uniform(0.2, 1.5), 2),
                'riesgo': riesgo,
                'kpi_source': "Simulación AI v2",
                'kpi_last_updated': datetime.utcnow()
            }
            
            try:
                kpi_entry = AdvancedKPI(**kpi_data)
                
                # El patrón correcto para un upsert con SQLAlchemy
                # session.merge() revisa la clave primaria, si existe, actualiza. Si no, inserta.
                db.session.merge(kpi_entry)
                db.session.commit()
                
                logger.info(f"KPI para '{nemo}' guardado en la base de datos via merge.")
                return kpi_data
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al guardar KPI para '{nemo}' en la base de datos: {e}")
                return None

def get_advanced_kpis(nemo: str) -> dict | None:
    """
    Simula la obtención de KPIs avanzados para un símbolo de acción.
    Actualmente devuelve datos de ejemplo.
    """
    logger.info(f"[AI Service] Solicitando KPIs para '{nemo}' (simulado).")
    
    # En una implementación real:
    # 1. Cargar configuración de API y prompt desde el modelo PromptConfig.
    # 2. Formatear el prompt con el 'nemo' y datos de cierre.
    # 3. Llamar a la API de la IA.
    # 4. Parsear la respuesta y devolverla.
    
    # Datos de ejemplo con la nueva estructura detallada:
    import random
    
    # Devolver None ocasionalmente para simular fallos
    if random.random() < 0.1:
        logger.warning(f"[AI Service] Simulación de fallo para '{nemo}'.")
        return None

    recommendations = ["Comprar", "Mantener", "Vender"]
    
    example_data = {
        "kpis": {
            "roe": round(random.uniform(5.0, 25.0), 2),
            "beta": round(random.uniform(0.5, 1.8), 2),
            "debt_to_equity": round(random.uniform(0.2, 1.5), 2)
        },
        "analyst_recommendation": random.choice(recommendations),
        "main_source": "Yahoo Finance (Simulado)",
        "details": {
            "roe": {
                "source": "Reporte Anual Simulado 2023",
                "calculation": "Se calculó como (Utilidad Neta / Patrimonio Neto Promedio) basado en datos simulados."
            },
            "beta": {
                "source": "Análisis de Mercado Simulado",
                "calculation": "Covarianza simulada de los retornos de la acción con los del mercado (IPSA) sobre la varianza de los retornos del mercado en los últimos 3 años."
            },
            "debt_to_equity": {
                "source": "Balance General Simulado Q2 2024",
                "calculation": "(Deuda Total / Patrimonio Neto). Los datos son proyecciones simuladas."
            },
            "analyst_recommendation": {
                "source": "Consenso de Analistas (Bloomberg simulado)",
                "calculation": "Basado en un promedio ponderado de 10 analistas simulados."
            }
        }
    }
        
    return example_data