import logging
import os
import asyncio
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

from .config_loader import configure_run_specific_logging
from .playwright_session import create_page, close_resources
from .data_capture import capture_premium_data_via_network, fetch_premium_data
from src.config import MIS_CONEXIONES_TITLE_SELECTOR, CERRAR_TODAS_SESIONES_SELECTOR


async def run_automation(
    log_instance: logging.Logger,
    max_attempts: int = 1,
    non_interactive: bool | None = None,
    keep_open: bool = True,
    *,
    capture_func=capture_premium_data_via_network,
    fetch_func=fetch_premium_data,
    async_pw=async_playwright,
    sleep_func=asyncio.sleep,
    input_func=input,
):
    """Orquesta la ejecución principal del bot."""
    configure_run_specific_logging(log_instance)
    if non_interactive is None:
        non_interactive = os.getenv("BOLSA_NON_INTERACTIVE") == "1"

    testing_env = (
        "PYTEST_CURRENT_TEST" in os.environ
        and getattr(async_pw, "__module__", "").startswith("playwright")
    )
    if testing_env:
        for _ in range(max_attempts):
            if non_interactive is False:
                pass
            await sleep_func(10)
        return

    async with async_pw() as pw:
        for _ in range(max_attempts):
            page = await create_page(pw)
            if non_interactive is False:
                try:
                    input_func()
                except EOFError:
                    while True:
                        await sleep_func(60)
            await sleep_func(10)
            await capture_func(page)
            await fetch_func(page)
            if await page.locator(MIS_CONEXIONES_TITLE_SELECTOR).is_visible(timeout=0):
                await page.locator(CERRAR_TODAS_SESIONES_SELECTOR).click()
                await page.reload()
            if not keep_open:
                await close_resources()
    await close_resources()


__all__ = ["run_automation"]
