# src/scripts/bot_config.py
import random

# Lista de User-Agents realistas para rotar en cada nueva sesión
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/126.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

def get_playwright_context_options(storage_state_path: str | None = None) -> dict:
    """
    Devuelve un diccionario de opciones para crear un nuevo contexto de Playwright,
    incluyendo user-agent, viewport y el estado de la sesión si existe.
    """
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "es-CL,es",
        "java_script_enabled": True,
        "accept_downloads": False,
        "storage_state": storage_state_path
    }

def get_extra_headers() -> dict:
    """Devuelve cabeceras HTTP adicionales para simular un navegador real."""
    return {
        "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }