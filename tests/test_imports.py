"""
tests/test_imports.py
─────────────────────
Pruebas unitarias básicas para garantizar que los módulos y funciones
críticas del proyecto puedan importarse sin errores.

Ejecuta con:
    pytest                     # todos los tests del proyecto
    pytest tests/test_imports.py   # solo este archivo
"""

import importlib
import pytest


# ------------- tabla de rutas y atributos que se deben poder importar ------------
IMPORT_TARGETS = [
    ("src.scripts.browser_refresh", "refresh_chromium_tab"),
    ("src.automatizacion_bolsa", "clean_percentage"),
    ("src.automatizacion_bolsa", "run_automation"),  # ← ahora desde el paquete
    # Añade más pares (módulo, atributo) si lo necesitas:
    # ("src.otra_ruta.modulo", "función_o_clase"),
]

@pytest.mark.parametrize("module_path, attribute", IMPORT_TARGETS)
def test_module_attribute_exists(module_path: str, attribute: str):
    """
    Verifica que:
      1. El módulo `module_path` pueda importarse sin lanzar excepciones.
      2. El atributo `attribute` exista dentro del módulo.
    """
    module = importlib.import_module(module_path)
    assert hasattr(module, attribute), f"'{attribute}' no encontrado en {module_path}"
