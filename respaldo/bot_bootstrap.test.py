import pytest
from src.scripts.bot_page_manager import get_page, close_browser

@pytest.mark.asyncio
@pytest.mark.integration
async def test_can_initialize_and_get_page():
    """
    Verifica que el PageManager puede obtener una página de Playwright.
    Esto implica que Playwright se instala y se puede lanzar un navegador.
    """
    page = None
    try:
        page = await get_page()
        assert page is not None, "La página obtenida no debería ser nula"
        assert not page.is_closed(), "La página no debería estar cerrada después de ser creada"
        
        # Opcional: una verificación simple de que la página está 'viva'
        await page.goto("about:blank")
        assert page.url == "about:blank", "La página no pudo navegar a 'about:blank'"
        
    finally:
        # Asegurarse de que todos los recursos de playwright se cierren
        await close_browser() 