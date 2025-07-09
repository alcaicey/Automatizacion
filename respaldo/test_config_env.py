import os
import pytest
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env si existe
load_dotenv()

@pytest.mark.prelaunch
def test_crucial_env_variables_are_present():
    """
    Verifica que las variables de entorno críticas para la operación
    de la aplicación están definidas.
    """
    required_vars = [
        "BOLSA_USERNAME",
        "BOLSA_PASSWORD",
        "DATABASE_URL"
    ]
    
    missing_vars = [var for var in required_vars if os.getenv(var) is None]
    
    assert not missing_vars, (
        f"Faltan las siguientes variables de entorno críticas: {', '.join(missing_vars)}. "
        "Asegúrate de que el archivo .env esté configurado correctamente."
    ) 