# run_bot_process.py
import asyncio
import os
import logging
from dotenv import load_dotenv

# --- IMPORTANTE: NO USAR eventlet.monkey_patch() aquí ---

# 1. Importar las funciones necesarias para crear la app
from src.app import create_app
from src.services.bolsa_service import run_bolsa_bot
from src.utils.logging_config import setup_logging

# Cargar variables de entorno desde el archivo .env
load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

async def run_bot_standalone():
    """
    Crea un contexto de aplicación Flask y ejecuta el bot de forma independiente.
    """
    logger.info("🤖 Iniciando ejecución del bot de scraping en un proceso separado...")
    
    # 2. Crear una instancia de la aplicación Flask
    app = create_app()

    # 3. Empujar un contexto de aplicación para poder usar db, etc.
    with app.app_context():
        try:
            username = os.getenv("BOLSA_USERNAME")
            password = os.getenv("BOLSA_PASSWORD")
            
            if not username or not password:
                logger.error("Error: Las variables de entorno BOLSA_USERNAME y BOLSA_PASSWORD no están configuradas.")
                return

            # 4. Pasar la instancia de 'app' a la función del bot
            await run_bolsa_bot(app=app, username=username, password=password)
            
            logger.info("✅ Proceso del bot finalizado con éxito.")

        except Exception as e:
            logger.critical(f"💥 Ocurrió un error no controlado durante la ejecución del bot: {e}", exc_info=True)


if __name__ == "__main__":
    # 5. Iniciar el loop de eventos de asyncio para ejecutar la corrutina principal
    try:
        asyncio.run(run_bot_standalone())
    except KeyboardInterrupt:
        logger.info("Ejecución del bot interrumpida por el usuario.") 