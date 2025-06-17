from __future__ import annotations
import asyncio
import logging
import os
import psutil
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright, BrowserContext, Error as PlaywrightError

_LOG = logging.getLogger(__name__)

_PLAYWRIGHT: Optional[Playwright] = None
_BROWSER: Optional[Browser] = None
_PAGE: Optional[Page] = None
_CONTEXT: Optional[BrowserContext] = None

# Puerto para el protocolo de depuración de Chrome (CDP)
CDP_PORT = 9222
CDP_ENDPOINT = f"http://localhost:{CDP_PORT}"
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".bolsa_santiago_bot")

def _is_browser_process_running() -> bool:
    """
    Verifica si hay un proceso de Chrome/Chromium corriendo con el puerto de depuración remoto abierto.
    """
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            # Buscamos un proceso de chrome que tenga el argumento del puerto de depuración
            if proc.info['name'] in ('chrome.exe', 'chromium.exe', 'msedge.exe') and proc.info['cmdline']:
                if f'--remote-debugging-port={CDP_PORT}' in proc.info['cmdline']:
                    _LOG.info(f"[PageManager] Proceso de navegador encontrado con PID {proc.pid} y puerto {CDP_PORT}.")
                    return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False

async def _get_playwright_instance() -> Playwright:
    """Inicia y devuelve la instancia singleton de Playwright."""
    global _PLAYWRIGHT
    if _PLAYWRIGHT is None:
        _LOG.info("[PageManager] Inicializando instancia principal de Playwright...")
        _PLAYWRIGHT = await async_playwright().start()
    return _PLAYWRIGHT

async def get_page() -> Page:
    """
    Punto de entrada principal. Se conecta a un navegador existente si es posible,
    o lanza uno nuevo si no hay ninguno.
    """
    global _BROWSER, _PAGE, _CONTEXT
    pw = await _get_playwright_instance()

    # Si ya tenemos una conexión de página válida, la reutilizamos.
    if _PAGE and not _PAGE.is_closed():
        _LOG.info("[PageManager] ✓ Reutilizando conexión de página existente.")
        return _PAGE

    # Intentar conectarse a un navegador ya abierto
    if _is_browser_process_running():
        _LOG.info(f"[PageManager] 🟢 Proceso de navegador detectado. Intentando conectar a {CDP_ENDPOINT}...")
        try:
            browser = await pw.chromium.connect_over_cdp(CDP_ENDPOINT)
            _LOG.info("[PageManager] ✓ Conexión sobre CDP exitosa.")
            _BROWSER = browser
            _CONTEXT = _BROWSER.contexts[0]
            _PAGE = _CONTEXT.pages[0] if _CONTEXT.pages else await _CONTEXT.new_page()
            return _PAGE
        except PlaywrightError as e:
            _LOG.warning(f"[PageManager] Falló la conexión sobre CDP: {e}. Se lanzará un nuevo navegador.")

    # Si no hay navegador o la conexión falló, lanzar uno nuevo.
    _LOG.info("[PageManager] 🚀 No hay navegador activo o la conexión falló. Lanzando nueva instancia...")
    
    # --- INICIO DE LA CORRECCIÓN: Volver a launch_persistent_context ---
    # Este método es el correcto para manejar perfiles de usuario y es más estable.
    # Le pasamos el argumento para que abra el puerto de depuración.
    _CONTEXT = await pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=[f"--remote-debugging-port={CDP_PORT}", "--start-maximized"]
    )
    # --- FIN DE LA CORRECCIÓN ---
    
    _BROWSER = _CONTEXT.browser
    _PAGE = _CONTEXT.pages[0] if _CONTEXT.pages else await _CONTEXT.new_page()
    
    _LOG.info(f"[PageManager] ✓ Nuevo navegador lanzado con perfil persistente y escuchando en el puerto {CDP_PORT}.")
    
    return _PAGE

async def close_browser() -> None:
    """Cierra todos los recursos de Playwright de forma ordenada."""
    global _BROWSER, _PLAYWRIGHT, _PAGE, _CONTEXT
    _LOG.info("[PageManager] Iniciando cierre de recursos de Playwright...")
    
    # El contexto persistente debe cerrarse. Esto también cierra el navegador.
    if _CONTEXT:
        await _CONTEXT.close()
        _LOG.info("[PageManager] ✓ Contexto y Navegador cerrados.")
    
    if _PLAYWRIGHT:
        await _PLAYWRIGHT.stop()
        _LOG.info("[PageManager] ✓ Instancia de Playwright detenida.")
        
    _BROWSER, _PLAYWRIGHT, _PAGE, _CONTEXT = None, None, None, None