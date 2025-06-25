from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright, BrowserContext

# Importamos la CLASE principal, como indica la documentación de la v2.0.0
from playwright_stealth import Stealth

from src.config import STORAGE_STATE_PATH
from .bot_config import get_playwright_context_options, get_extra_headers

_LOG = logging.getLogger(__name__)

# Variables globales
_PLAYWRIGHT: Optional[Playwright] = None
_BROWSER: Optional[Browser] = None
_PAGE: Optional[Page] = None
_CONTEXT: Optional[BrowserContext] = None

async def _get_playwright_instance() -> Playwright:
    """Inicia y devuelve la instancia singleton de Playwright."""
    global _PLAYWRIGHT
    if _PLAYWRIGHT is None:
        _LOG.info("[PageManager] Inicializando instancia principal de Playwright...")
        _PLAYWRIGHT = await async_playwright().start()
    return _PLAYWRIGHT

async def get_page() -> Page:
    """
    Punto de entrada principal. Crea un nuevo contexto y página aplicando
    configuraciones de evasión y reutilizando el estado de la sesión.
    """
    global _BROWSER, _PAGE, _CONTEXT
    pw = await _get_playwright_instance()

    if _PAGE and not _PAGE.is_closed():
        _LOG.info("[PageManager] ✓ Reutilizando conexión de página existente.")
        return _PAGE
        
    if _BROWSER and _BROWSER.is_connected():
        _LOG.info("[PageManager] Reutilizando instancia de navegador existente.")
    else:
        _LOG.info("[PageManager] 🚀 Lanzando nueva instancia de navegador...")
        _BROWSER = await pw.chromium.launch(headless=False)

    storage_state = STORAGE_STATE_PATH if os.path.exists(STORAGE_STATE_PATH) else None
    if storage_state:
        _LOG.info(f"[PageManager] Estado de sesión encontrado en {STORAGE_STATE_PATH}. Se cargará.")
    
    context_options = get_playwright_context_options(storage_state_path=storage_state)
    _CONTEXT = await _BROWSER.new_context(**context_options)
    
    _CONTEXT.on("close", _save_session_state_sync_wrapper)
    
    # --- INICIO DE LA CORRECCIÓN SEGÚN DOCUMENTACIÓN v2.0.0 ---
    # 1. Creamos una instancia de la clase Stealth.
    stealth_config = Stealth()
    # 2. Aplicamos el stealth al CONTEXTO usando el método `apply_stealth_async`.
    await stealth_config.apply_stealth_async(_CONTEXT)
    # --- FIN DE LA CORRECCIÓN ---

    _PAGE = await _CONTEXT.new_page()
    await _PAGE.set_extra_http_headers(get_extra_headers())
    
    _LOG.info("[PageManager] ✓ Nuevo contexto y página creados con evasión aplicada.")
    
    return _PAGE

def _save_session_state_sync_wrapper():
    """Wrapper síncrono para poder llamarlo desde el evento 'on close'."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_save_session_state())
    except RuntimeError:
        asyncio.run(_save_session_state())

async def _save_session_state():
    """Guarda el estado actual del contexto (cookies, etc.) en un archivo."""
    if _CONTEXT:
        try:
            await _CONTEXT.storage_state(path=STORAGE_STATE_PATH)
            _LOG.info(f"[PageManager] ✓ Estado de la sesión guardado exitosamente en {STORAGE_STATE_PATH}")
        except Exception as e:
            _LOG.error(f"[PageManager] No se pudo guardar el estado de la sesión: {e}")

async def close_browser() -> None:
    """Cierra todos los recursos de Playwright de forma ordenada, guardando la sesión."""
    global _BROWSER, _PLAYWRIGHT, _PAGE, _CONTEXT
    _LOG.info("[PageManager] Iniciando cierre de recursos de Playwright...")
    
    await _save_session_state()

    if _CONTEXT and not _CONTEXT.is_closed():
        await _CONTEXT.close()
    if _BROWSER and _BROWSER.is_connected():
        await _BROWSER.close()
    if _PLAYWRIGHT:
        await _PLAYWRIGHT.stop()
        
    _BROWSER, _PLAYWRIGHT, _PAGE, _CONTEXT = None, None, None, None
    _LOG.info("[PageManager] ✓ Recursos de Playwright cerrados.")