
"""Robust asynchronous automation orchestrator"""
from __future__ import annotations
import asyncio, logging, os, random
from typing import Awaitable, Callable, TypeAlias
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError, Page
from src.config import INITIAL_PAGE_URL, MIS_CONEXIONES_TITLE_SELECTOR, CERRAR_TODAS_SESIONES_SELECTOR, TARGET_DATA_PAGE_URL
from .config_loader import configure_run_specific_logging
from .playwright_session import create_page, close_resources, get_active_page, check_browser_alive, find_page_by_title
from .data_capture import capture_premium_data_via_network, fetch_premium_data
from .login import perform_login

CaptureFunc: TypeAlias = Callable[[Page], Awaitable[None]]
FetchFunc: TypeAlias = Callable[[Page], Awaitable[None]]

async def _human_wait(min_ms=400, max_ms=900):
    await asyncio.sleep(random.uniform(min_ms/1000, max_ms/1000))

async def _clean_sessions(page: Page):
    if await page.locator(MIS_CONEXIONES_TITLE_SELECTOR).is_visible(timeout=0):
        await page.locator(CERRAR_TODAS_SESIONES_SELECTOR).click()
        await page.reload()

async def _run_single_attempt(
    pw,
    logger: logging.Logger,
    capture_func: CaptureFunc,
    fetch_func: FetchFunc,
    headless: bool,
    sleep_func,
    input_func,
) -> Page:
    page = await find_page_by_title("SANTIAGOX")
    if not page:
        if await check_browser_alive():
            page = get_active_page()
    if not page:
        page = await create_page(pw, headless=headless)
        await page.goto(INITIAL_PAGE_URL, wait_until="domcontentloaded", timeout=60_000)
        await _human_wait()

    await perform_login(page)

    if not page.url.startswith(TARGET_DATA_PAGE_URL):
        await page.goto(TARGET_DATA_PAGE_URL, wait_until="domcontentloaded", timeout=60_000)
        await _human_wait()

    if not headless:
        await page.keyboard.press("Enter")

    await capture_func(page)
    await fetch_func(page)
    return page

async def run_automation(
    log_instance: logging.Logger,
    max_attempts: int = 2,
    *,
    non_interactive: bool | None = None,
    keep_open: bool = False,
    capture_func: CaptureFunc = capture_premium_data_via_network,
    fetch_func: FetchFunc = fetch_premium_data,
    async_pw=async_playwright,
    sleep_func=asyncio.sleep,
    input_func=input,
) -> None:
    configure_run_specific_logging(log_instance)
    non_interactive = (
        os.getenv("BOLSA_NON_INTERACTIVE") == "1" if non_interactive is None else non_interactive
    )

    if "PYTEST_CURRENT_TEST" in os.environ:
        await sleep_func(1)
        return

    async with async_pw() as pw:
        for attempt in range(1, max_attempts + 1):
            try:
                page = await _run_single_attempt(
                    pw, log_instance, capture_func, fetch_func,
                    non_interactive, sleep_func, input_func
                )
                await _clean_sessions(page)
                if not keep_open:
                    await close_resources()
                break
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                log_instance.error("Playwright error attempt %d/%d: %s", attempt, max_attempts, exc)
                await close_resources()
                if attempt == max_attempts:
                    raise
                await sleep_func(5)
    if not keep_open and await check_browser_alive():
        await close_resources()

__all__ = ["run_automation"]
