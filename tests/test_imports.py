"""
tests/test_imports.py
─────────────────────
Prueba de “sanidad” de imports.

Comprueba que todos los módulos críticos del pipeline Bolsa-Santiago
pueden importarse sin lanzar excepciones en el entorno actual.

Añade o quita rutas de módulo en la lista MODULES según evolucione
el proyecto.
"""
from __future__ import annotations

import importlib
import pytest

# Lista exhaustiva de módulos que deben poder importarse
MODULES = [
    # ───── Núcleo de automatización (Playwright) ─────
    "src.scripts.bolsa_santiago_bot",      # :contentReference[oaicite:0]{index=0}
    "src.scripts.bolsa_service",      # :contentReference[oaicite:0]{index=0}
    "src.automatizacion_bolsa.login",               # :contentReference[oaicite:1]{index=1}
    "src.automatizacion_bolsa.playwright_session",  # :contentReference[oaicite:2]{index=2}
    "src.automatizacion_bolsa.config_loader",  # :contentReference[oaicite:2]{index=2}
    "src.automatizacion_bolsa.data_capture",  # :contentReference[oaicite:2]{index=2}
    "src.automatizacion_bolsa.page_manager",  # :contentReference[oaicite:2]{index=2}
    "src.automatizacion_bolsa.playwright_session",  # :contentReference[oaicite:2]{index=2}

    # ───── Adaptadores / wrappers usados por el servicio ─────
    "src.scripts.bolsa_santiago_bot",               # :contentReference[oaicite:3]{index=3}
    "src.scripts.bolsa_service",                    # :contentReference[oaicite:4]{index=4}
    "src.scripts.har_analyzer",

    # ───── Utilidades y helpers invocados indirectamente ─────
    "src.utils.db_io",          # utilidades de E/S y orquestación
    "src.config",               # constantes de selectores, URLs, etc.
]

@pytest.mark.parametrize("module_name", MODULES)
def test_import_module(module_name: str) -> None:
    """
    La prueba pasa si cada módulo se importa sin errores.
    """
    importlib.import_module(module_name)
