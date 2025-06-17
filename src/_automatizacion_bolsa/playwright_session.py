"""
playwright_session.py
────────────────────────────────────────────────────────────
Super-thin wrapper sobre page_manager para mantener compatibilidad
con el resto del proyecto.
"""

from __future__ import annotations
import logging
from typing import Optional
from playwright.async_api import Page
from .page_manager import get_page, close_browser

_LOG = logging.getLogger(__name__)

async def create_page(*_, headless: bool = False) -> Page:
    """Delega en page_manager, conservando la firma para compatibilidad."""
    if headless:
        _LOG.warning("create_page(): parámetro headless ignorado (browser persistente).")
    return await get_page()

def get_active_page() -> Optional[Page]:
    """No se usa en el flujo refactorizado, se mantiene por si acaso."""
    _LOG.warning("get_active_page() está deprecado, usar get_page() asíncrono.")
    return None

def check_browser_alive() -> bool:
    """True si el Browser global sigue conectado."""
    # Esta función debería ser implementada en page_manager si se necesita
    _LOG.warning("check_browser_alive() no está implementado en el nuevo flujo.")
    return False

async def close_resources() -> None:
    """Cierra todos los recursos de Playwright gestionados por page_manager."""
    _LOG.info("Cerrando recursos de Playwright a través de la sesión...")
    await close_browser()