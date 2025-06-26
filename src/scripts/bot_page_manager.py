# src/scripts/bot_page_manager.py

from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright, BrowserContext
from playwright_stealth import Stealth

from src.config import STORAGE_STATE_PATH
# --- INICIO DE LA MODIFICACIÓN: Importar nueva función de config ---
from .bot_config import get_playwright_context_options, get_extra_headers, get_browser_launch_options
# --- FIN DE LA MODIFICACIÓN ---

_LOG = logging.getLogger(__name__)

_PLAYWRIGHT: Optional[Playwright] = None
_BROWSER: Optional[Browser] = None
_PAGE: Optional[Page] = None
_CONTEXT: Optional[BrowserContext] = None
_page_creation_lock = asyncio.Lock()

async def _get_playwright_instance() -> Playwright:
    global _PLAYWRIGHT
    if _PLAYWRIGHT is None:
        _LOG.info("[PageManager] Inicializando instancia principal de Playwright...")
        _PLAYWRIGHT = await async_playwright().start()
    return _PLAYWRIGHT

async def recreate_page() -> Page:
    global _PAGE, _CONTEXT
    
    async with _page_creation_lock:
        _LOG.warning("[PageManager] Solicitud para recrear la página. Cerrando instancias actuales si existen...")
        
        if _PAGE and not _PAGE.is_closed():
            try: await _PAGE.close()
            except Exception as e: _LOG.error(f"[PageManager] Error al cerrar página existente: {e}")
        
        if _CONTEXT:
             try:
                await _CONTEXT.close()
             except Exception as e:
                _LOG.error(f"[PageManager] Error al cerrar contexto existente: {e}")

        _PAGE = None
        _CONTEXT = None
        _LOG.info("[PageManager] Instancias de página y contexto limpiadas.")
    
    return await get_page()

async def get_page() -> Page:
    global _BROWSER, _PAGE, _CONTEXT
    
    async with _page_creation_lock:
        if _PAGE and not _PAGE.is_closed():
            _LOG.info("[PageManager] ✓ Reutilizando conexión de página existente.")
            return _PAGE
            
        pw = await _get_playwright_instance()
        
        if not (_BROWSER and _BROWSER.is_connected()):
            _LOG.info("[PageManager] 🚀 Lanzando nueva instancia de navegador Chromium con opciones de evasión...")
            # --- INICIO DE LA MODIFICACIÓN: Usar nuevas opciones de lanzamiento ---
            launch_options = get_browser_launch_options()
            _BROWSER = await pw.chromium.launch(**launch_options)
            # --- FIN DE LA MODIFICACIÓN ---

        storage_state = STORAGE_STATE_PATH if os.path.exists(STORAGE_STATE_PATH) else None
        if storage_state: _LOG.info(f"[PageManager] Estado de sesión encontrado. Se cargará.")
        
        context_options = get_playwright_context_options(storage_state_path=storage_state)
        _LOG.info("[PageManager] Creando nuevo contexto de navegador...")
        _CONTEXT = await _BROWSER.new_context(**context_options)
        
        _LOG.info("[PageManager] Aplicando capa de evasión (stealth)...")
        stealth_instance = Stealth()
        await stealth_instance.apply_stealth_async(_CONTEXT)

        _CONTEXT.on("close", _save_session_state_sync_wrapper)

        _LOG.info("[PageManager] Creando una nueva página desde el contexto modificado...")
        _PAGE = await _CONTEXT.new_page()
        
        await _PAGE.set_extra_http_headers(get_extra_headers())
        
        _LOG.info("[PageManager] ✓ Página creada y configurada con éxito. Lista para navegar.")
        
        return _PAGE

def _save_session_state_sync_wrapper():
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            loop.create_task(_save_session_state())
        else:
            asyncio.run(_save_session_state())
    except RuntimeError:
        asyncio.run(_save_session_state())

async def _save_session_state():
    try:
        if _CONTEXT and _CONTEXT.pages:
            await _CONTEXT.storage_state(path=STORAGE_STATE_PATH)
            _LOG.info(f"[PageManager] ✓ Estado de la sesión guardado exitosamente en {STORAGE_STATE_PATH}")
    except Exception as e:
        _LOG.error(f"[PageManager] No se pudo guardar el estado de la sesión (probablemente ya estaba cerrado): {e}")

async def close_browser() -> None:
    global _BROWSER, _PLAYWRIGHT, _PAGE, _CONTEXT
    _LOG.info("[PageManager] Iniciando cierre de recursos de Playwright...")
    
    await _save_session_state()

    try:
        if _PAGE and not _PAGE.is_closed(): await _PAGE.close()
        if _CONTEXT: await _CONTEXT.close()
        if _BROWSER and _BROWSER.is_connected(): await _BROWSER.close()
        if _PLAYWRIGHT: await _PLAYWRIGHT.stop()
    except Exception as e:
        _LOG.error(f"Error durante el cierre limpio de Playwright: {e}")
        
    _BROWSER, _PLAYWRIGHT, _PAGE, _CONTEXT = None, None, None, None
    _LOG.info("[PageManager] ✓ Recursos de Playwright cerrados.")