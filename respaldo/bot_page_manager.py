# src/scripts/bot_page_manager.py

import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright, BrowserContext
# from playwright_stealth import stealth_async # MANTENIDO COMENTADO

from src.config import STORAGE_STATE_PATH
from .bot_config import get_playwright_context_options, get_browser_launch_options

_LOG = logging.getLogger(__name__)

class PageManager:
    _instance: Optional['PageManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized: return
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = True
        _LOG.info("[PageManager] Instancia Singleton de PageManager creada.")

    @classmethod
    async def get_instance(cls) -> 'PageManager':
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def get_page(self) -> Page:
        """
        Obtiene una página de Playwright válida, validando activamente la conexión
        y recreando componentes si es necesario. Lógica corregida.
        """
        # Si la página ya existe y no está explícitamente cerrada, debemos validarla.
        if self.page and not self.page.is_closed():
            try:
                # La prueba de fuego: si esto funciona, la página está viva.
                await self.page.title()
                _LOG.info("[PageManager] ✓ Página existente validada activamente. Reutilizando.")
                return self.page
            except Exception as e:
                # Capturamos CUALQUIER error (incluido AttributeError) como señal de que la página es un zombie.
                _LOG.warning(f"[PageManager] La página parecía viva pero no respondió (Error: {type(e).__name__}). Se recreará.")
                # No hacemos nada más aquí, dejaremos que el código de abajo la recree.

        # Si llegamos aquí, es porque:
        # 1. No había página (self.page es None).
        # 2. La página estaba cerrada (self.page.is_closed() es True).
        # 3. La validación activa falló.
        # En todos estos casos, necesitamos una nueva página.
        await self._ensure_browser_and_context()
        await self._create_page()
        
        assert self.page, "La página no pudo ser creada."
        return self.page

    async def _ensure_browser_and_context(self):
        """Asegura que el navegador y el contexto estén listos antes de crear una página."""
        if not self.browser or not self.browser.is_connected():
            await self.close() # Cierra todo para empezar de cero.
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(**get_browser_launch_options())
            storage_state = STORAGE_STATE_PATH if os.path.exists(STORAGE_STATE_PATH) else None
            self.context = await self.browser.new_context(**get_playwright_context_options(storage_state_path=storage_state))

    async def _create_page(self):
        """Crea una nueva página y le aplica stealth."""
        assert self.context, "Contexto no inicializado."
        self.page = await self.context.new_page()
        _LOG.info("[PageManager] Aplicando capa de evasión (stealth)...")
        # await stealth_async(self.page) # MANTENIDO COMENTADO
        _LOG.info("[PageManager] ✓ Nueva página creada y configurada.")

    async def close(self):
        _LOG.info("[PageManager] Iniciando cierre de recursos de Playwright...")
        closables = [self.page, self.context, self.browser, self.playwright]
        if self.context and self.context.pages:
            try: await self.context.storage_state(path=STORAGE_STATE_PATH)
            except Exception: pass
        for resource in closables:
            if resource:
                try:
                    close_method = getattr(resource, 'stop', getattr(resource, 'close'))
                    if not getattr(resource, 'is_closed', lambda: False)():
                         await close_method()
                except Exception: continue
        self.playwright, self.browser, self.context, self.page = None, None, None, None
        _LOG.info("[PageManager] ✓ Recursos de Playwright cerrados.")

async def get_page_manager_instance() -> PageManager:
    return await PageManager.get_instance()