from playwright.sync_api import Page

from src.config import (
    USERNAME,
    PASSWORD,
    USERNAME_SELECTOR,
    PASSWORD_SELECTOR,
    LOGIN_BUTTON_SELECTOR,
)
from .config_loader import logger


def perform_login(page: Page) -> None:
    """Realiza el proceso de login estándar."""
    logger.info("Realizando login en Bolsa de Santiago")
    page.fill(USERNAME_SELECTOR, USERNAME)
    page.fill(PASSWORD_SELECTOR, PASSWORD)
    page.click(LOGIN_BUTTON_SELECTOR)


__all__ = ["perform_login"]
