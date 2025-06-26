# src/scripts/bot_config.py
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/126.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

# --- INICIO DE LA MODIFICACIÓN: Argumentos de lanzamiento para evasión ---
def get_browser_launch_options() -> dict:
    """Devuelve un diccionario de opciones para el lanzamiento del navegador."""
    return {
        "headless": False,
        "args": [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--start-maximized',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
# --- FIN DE LA MODIFICACIÓN ---


def get_playwright_context_options(storage_state_path: str | None = None) -> dict:
    """
    Devuelve un diccionario de opciones para crear un nuevo contexto de Playwright.
    """
    # --- INICIO DE LA MODIFICACIÓN: Ajustes de contexto para evasión ---
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": None,  # Usar 'None' cuando se lanza maximizado con '--start-maximized'
        "locale": "es-CL,es;q=0.9",
        "java_script_enabled": True,
        "accept_downloads": False,
        "storage_state": storage_state_path,
        "ignore_https_errors": True, # Ignora errores de certificado SSL, común en proxys/WAFs
        "bypass_csp": True, # Intenta saltar la Content Security Policy
    }
    # --- FIN DE LA MODIFICACIÓN ---

def get_extra_headers() -> dict:
    """Devuelve cabeceras HTTP adicionales para simular un navegador real."""
    # --- INICIO DE LA MODIFICACIÓN: Cabeceras más realistas ---
    return {
        "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
    # --- FIN DE LA MODIFICACIÓN ---