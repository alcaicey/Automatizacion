# src/scripts/bot_config.py
import datetime
import os
from datetime import time
import pytz
import random

# URL base para la navegación y login
BASE_URL = "https://www.bolsadesantiago.com"

# URL específica de la página de datos de acciones que se usará para el scraping
TARGET_DATA_PAGE_URL = os.getenv("TARGET_DATA_PAGE_URL", "https://www.bolsadesantiago.com/resumen_mercado/resumen/acciones")

# Define la zona horaria de Santiago
SANTIAGO_TZ = pytz.timezone('America/Santiago')

# Horas de apertura y cierre del mercado bursátil chileno
MARKET_OPEN_TIME = time(9, 30, tzinfo=SANTIAGO_TZ)
MARKET_CLOSE_TIME = time(16, 0, tzinfo=SANTIAGO_TZ)

# --- URLs y Fragmentos ---
LOGIN_LANDING_PAGE_URL = f"{BASE_URL}/login"
ACTIVE_SESSIONS_URL_FRAGMENT = "Control/sesionesactivas"
SSO_URL_FRAGMENT = "sso.bolsadesantiago.com"

# --- Selectores CSS ---
HEADER_LOGIN_LINK_SELECTOR = '#menuppal-login a'
LOGIN_PAGE_BUTTON_SELECTOR = 'button.btn:has-text("Ingresar")'
USER_INPUT_SELECTOR = "#username"
PASSWORD_INPUT_SELECTOR = "#password"
SUBMIT_BUTTON_SELECTOR = "input[type='submit']"
NAVBAR_TOGGLER_SELECTOR = 'button.navbar-toggler'
CLOSE_ALL_SESSIONS_BUTTON_SELECTOR = 'a.btn.btn-primary[href*="cerrartodas"]'


# --- Configuraciones de Playwright (ya existentes) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/126.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

def get_browser_launch_options() -> dict:
    return {
        "headless": False,
        "args": [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--start-maximized',
            '--no-sandbox',
        ]
    }

def get_playwright_context_options(storage_state_path: str | None = None) -> dict:
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": None,
        "locale": "es-CL,es;q=0.9",
        "storage_state": storage_state_path,
        "ignore_https_errors": True,
        "bypass_csp": True,
    }