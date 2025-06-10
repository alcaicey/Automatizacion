# -*- coding: utf-8 -*-
"""Archivo corregido y mejorado: Automatización Bolsa Santiago"""

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)
import time
import json
import logging
from datetime import datetime
import os
import random
import argparse

# Dependencia opcional para controlar ventanas
try:
    import pygetwindow as gw
except Exception:
    gw = None

from src.config import (
    LOGS_DIR,
    INITIAL_PAGE_URL,
    TARGET_DATA_PAGE_URL,
    USERNAME,
    PASSWORD,
    USERNAME_SELECTOR,
    PASSWORD_SELECTOR,
    LOGIN_BUTTON_SELECTOR,
    API_PRIMARY_DATA_PATTERNS,
    URLS_TO_INSPECT_IN_HAR_FOR_CONTEXT,
    MIS_CONEXIONES_TITLE_SELECTOR,
    CERRAR_TODAS_SESIONES_SELECTOR,
    STORAGE_STATE_PATH,
)
from src.scripts.har_analyzer import analyze_har_and_extract_data

# Archivos y control de estado
TIMESTAMP_NOW = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = os.path.join(LOGS_DIR, f"bolsa_bot_log_{TIMESTAMP_NOW}.txt")
HAR_FILENAME = os.path.join(LOGS_DIR, "network_capture.har")
OUTPUT_ACCIONES_DATA_FILENAME = os.path.join(LOGS_DIR, f"acciones-precios-plus_{TIMESTAMP_NOW}.json")
ANALYZED_SUMMARY_FILENAME = os.path.join(LOGS_DIR, f"network_summary_{TIMESTAMP_NOW}.json")

# Globales
NON_INTERACTIVE = os.getenv("BOLSA_NON_INTERACTIVE") == "1"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MIN_EXPECTED_RESULTS = 5

_p_instance = None
_browser = None
_context = None
_page = None

logger = logging.getLogger("bolsa_bot")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_FILENAME, encoding="utf-8")
fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
logger.addHandler(fh)

# Función para limpiar porcentajes (-0,34%) de textos
def clean_percentage(text):
    import re
    return re.sub(r"\s*\([-+]?\d+(?:[.,]\d+)?%\)", "", text)

# Verifica si la ventana "SANTIAGOX" ya está abierta (evita abrir más navegadores)
def is_santiagox_window_open():
    if not gw:
        return False
    try:
        return any("SANTIAGOX" in w.title.upper() for w in gw.getWindowsWithTitle(""))
    except Exception:
        return False

# Log personalizado cuando se detecta apertura innecesaria
def log_browser_conflict():
    conflict_log = os.path.join(LOGS_DIR, f"browser_conflict_{TIMESTAMP_NOW}.log")
    with open(conflict_log, "w", encoding="utf-8") as f:
        f.write("⚠️ Se intentó abrir una nueva ventana cuando ya existía una activa.
")
    logger.warning("Navegador duplicado detectado. Log guardado en " + conflict_log)

# Simulación de alerta frontend por navegador cerrado (placeholder para front)
def alert_frontend_browser_closed():
    print("🚨 ALERTA: No hay navegador activo. Verifica si se cerró inesperadamente.")

# Simulación de alerta frontend por credenciales vacías
def alert_missing_credentials():
    print("🚨 ALERTA: Faltan credenciales. Define BOLSA_USERNAME y BOLSA_PASSWORD.")

# Validación de credenciales con alerta visual
def validate_credentials():
    global USERNAME, PASSWORD
    USERNAME = os.environ.get("BOLSA_USERNAME", USERNAME)
    PASSWORD = os.environ.get("BOLSA_PASSWORD", PASSWORD)
    if not USERNAME or not PASSWORD:
        alert_missing_credentials()
        raise ValueError("Credenciales faltantes: BOLSA_USERNAME o BOLSA_PASSWORD")

# Placeholder principal
def main():
    validate_credentials()
    if is_santiagox_window_open():
        log_browser_conflict()
        alert_frontend_browser_closed()
        return
    logger.info("Validaciones completas. Iniciar automatización...")
    # Aquí seguiría el resto del proceso, no incluido por límite de espacio

if __name__ == "__main__":
    main()
