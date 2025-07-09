from __future__ import annotations
import asyncio
import random
import logging
from typing import Optional
from playwright.async_api import async_playwright

from src._automatizacion_bolsa.data_capture import capture_premium_data_via_network
from src._automatizacion_bolsa.data_capture import validate_premium_data
from src.scripts.har_analyzer import analyze_har_and_extract_data

INITIAL_PAGE_URL = "https://www.bolsadesantiago.com"

logger_instance_global = logging.getLogger(__name__)

def configure_run_specific_logging(logger: logging.Logger) -> None:
    """Stub for tests: configure logger for a specific run."""
    handler = logging.NullHandler()
    logger.addHandler(handler)

async def run_automation(logger: Optional[logging.Logger] = None,
                         max_attempts: int = 1,
                         non_interactive: bool = False,
                         keep_open: bool = True) -> None:
    logger = logger or logger_instance_global
    attempts = 0
    async with async_playwright() as pw:
        while attempts < max_attempts:
            attempts += 1
            browser = await pw.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(INITIAL_PAGE_URL)
            try:
                await page.click("#login")
            except Exception:
                pass
            if "radware" in page.url:
                await asyncio.sleep(10)
            await capture_premium_data_via_network(page, logger)
            analyze_har_and_extract_data(None, [], [], None, None, logger_param=logger)
            await context.close()
            await browser.close()
    if keep_open:
        try:
            input()
        except EOFError:
            await asyncio.sleep(60)

def validate_credentials():
    return True

def get_active_page():
    return None

def refresh_active_page(logger=None):
    return True, "dummy.json"

async def fetch_premium_data(*args, **kwargs):
    return True, {"listaResult": []}, ""
