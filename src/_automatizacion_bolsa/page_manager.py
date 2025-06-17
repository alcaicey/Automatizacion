# src/automatizacion_bolsa/page_manager.py

from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright

_LOG = logging.getLogger(__name__)

# --- Estado Global para una única instancia de Playwright y Navegador ---
_PLAYWRIGHT: Optional[Playwright] = None
_BROWSER: Optional[Browser] = None
_PAGE: Optional[Page] = None
_USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".bolsa_santiago_bot")

async def _get_playwright_instance() -> Playwright:
    """Inicia y devuelve la instancia singleton de Playwright."""
    global _PLAYWRIGHT
    if _PLAYWRIGHT is None or not _PLAYWRIGHT.is_connected():
        _LOG.info("[PageManager] Inicializando instancia principal de Playwright...")
        _PLAYWRIGHT = await async_playwright().start()
    return _PLAYWRIGHT

async def _launch_persistent() -> None:
    """Lanza un navegador con contexto persistente si no existe y lo mantiene vivo."""
    global _BROWSER, _PAGE
    
    _LOG.info("[PageManager] 🟢 Solicitud de navegador..." )
    
    if _BROWSER and _BROWSER.is_connected():
        _LOG.info("[PageManager] ✓ Reutilizando navegador existente.")
        if not _PAGE or _PAGE.is_closed():
            _LOG.info("[PageManager] La pestaña se cerró. Creando una nueva página en el navegador existente.")
            context = _BROWSER.contexts[0] if _BROWSER.contexts else await _BROWSER.new_context()
            _PAGE = context.pages[0] if context.pages else await context.new_page()
            _LOG.info("[PageManager] ✓ Nueva página creada/reutilizada.")
        return

    _LOG.info("[PageManager] 🚀 No hay navegador activo. Lanzando nueva instancia persistente...")
    pw = await _get_playwright_instance()
    
    context = await pw.chromium.launch_persistent_context(
        _USER_DATA_DIR,
        headless=False,
        args=["--start-maximized"],
    )

    # --- INICIO DE LA CORRECCIÓN VALIDADA ---
    # Se asigna el objeto del navegador a la variable global ANTES de usarlo.
    # Este es el paso que corrige el potencial AttributeError.
    _BROWSER = context.browser
    
    # Ahora que _BROWSER ya no es None, podemos registrar el evento de forma segura.
    if _BROWSER:
        _BROWSER.on("disconnected", lambda: _LOG.warning("[PageManager] 🔴 ALERTA: El navegador se ha desconectado."))
    # --- FIN DE LA CORRECCIÓN VALIDADA ---
    
    _PAGE = context.pages[0] if context.pages else await context.new_page()
    _LOG.info("[PageManager] ✓ Navegador persistente lanzado y listo.")


async def get_page() -> Page:
    """Punto de entrada principal para obtener la página del navegador persistente."""
    await _launch_persistent()
    if not _PAGE:
        raise RuntimeError("No se pudo obtener una página válida del navegador.")
    return _PAGE

async def close_browser() -> None:
    """Cierra todos los recursos de Playwright de forma ordenada al apagar el servidor."""
    global _BROWSER, _PLAYWRIGHT, _PAGE
    _LOG.info("[PageManager] Iniciando cierre de recursos de Playwright...")
    
    if _BROWSER and _BROWSER.is_connected():
        await _BROWSER.close()
        _LOG.info("[PageManager] ✓ Navegador cerrado.")
    if _PLAYWRIGHT and _PLAYWRIGHT.is_connected():
        await _PLAYWRIGHT.stop()
        _LOG.info("[PageManager] ✓ Instancia de Playwright detenida.")
        
    _BROWSER, _PLAYWRIGHT, _PAGE = None, None, None