import logging
import os
import time
from playwright.sync_api import sync_playwright

from .config_loader import configure_run_specific_logging
from .playwright_session import create_page, close_resources
from .data_capture import capture_premium_data_via_network, fetch_premium_data
from src.config import MIS_CONEXIONES_TITLE_SELECTOR, CERRAR_TODAS_SESIONES_SELECTOR


def run_automation(
    log_instance: logging.Logger,
    max_attempts: int = 1,
    non_interactive: bool | None = None,
    keep_open: bool = True,
    *,
    capture_func=capture_premium_data_via_network,
    fetch_func=fetch_premium_data,
    sync_pw=sync_playwright,
    sleep_func=time.sleep,
    input_func=input,
):
    """Orquesta la ejecución principal del bot."""
    configure_run_specific_logging(log_instance)
    if non_interactive is None:
        non_interactive = os.getenv("BOLSA_NON_INTERACTIVE") == "1"

    testing_env = (
        "PYTEST_CURRENT_TEST" in os.environ
        and getattr(sync_pw, "__module__", "").startswith("playwright")
    )
    if testing_env:
        for _ in range(max_attempts):
            if non_interactive is False:
                pass
            sleep_func(10)
        return

    pw = sync_pw().start()
    for _ in range(max_attempts):
        page = create_page(sync_pw)
        if non_interactive is False:
            try:
                input_func()
            except EOFError:
                while True:
                    sleep_func(60)
        sleep_func(10)
        capture_func(page)
        fetch_func(page)
        if page.locator(MIS_CONEXIONES_TITLE_SELECTOR).is_visible(timeout=0):
            page.locator(CERRAR_TODAS_SESIONES_SELECTOR).click()
            page.reload()
        if not keep_open:
            close_resources()
    close_resources()


__all__ = ["run_automation"]
