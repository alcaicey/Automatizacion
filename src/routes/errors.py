# src/routes/errors.py

from playwright.sync_api import Page, TimeoutError

def esperar_login(page: Page):
    try:
        page.wait_for_selector("#menuppal-login a", timeout=20000)
        return "Selector visible"
    except TimeoutError:
        raise TimeoutError("El botón de login no apareció dentro del tiempo esperado")
