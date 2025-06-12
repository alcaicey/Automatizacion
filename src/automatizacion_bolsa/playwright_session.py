
from __future__ import annotations

import asyncio
from typing import Optional

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

_PW: Optional[Playwright] = None
_BROWSER: Optional[Browser] = None
_CONTEXT: Optional[BrowserContext] = None
_LAST_PAGE: Optional[Page] = None


def _ensure_pw() -> Playwright:
    global _PW
    if _PW is None:
        _PW = asyncio.get_event_loop().run_until_complete(async_playwright().start())
    return _PW


async def create_page(pw: Playwright | None = None, *, headless: bool = True, context_kwargs: dict | None = None) -> Page:
    global _PW, _BROWSER, _CONTEXT, _LAST_PAGE
    if pw is None:
        pw = _ensure_pw()
    else:
        _PW = pw
    if _BROWSER is None:
        _BROWSER = await pw.chromium.launch(headless=headless)
    _CONTEXT = await _BROWSER.new_context(**(context_kwargs or {}))
    _LAST_PAGE = await _CONTEXT.new_page()
    return _LAST_PAGE


def get_active_page() -> Page | None:
    return _LAST_PAGE


async def check_browser_alive() -> bool:
    return bool(_CONTEXT and _CONTEXT.pages)


async def close_resources() -> None:
    global _PW, _BROWSER, _CONTEXT, _LAST_PAGE
    try:
        if _CONTEXT:
            await _CONTEXT.close()
    finally:
        _CONTEXT = None
        _LAST_PAGE = None
        if _BROWSER:
            await _BROWSER.close()
            _BROWSER = None
        if _PW:
            await _PW.stop()
            _PW = None


async def find_page_by_title(keyword: str) -> Page | None:
    if not _BROWSER:
        return None
    for context in _BROWSER.contexts:
        for page in context.pages:
            try:
                title = await page.title()
            except Exception:
                continue
            if keyword.lower() in title.lower():
                return page
    return None


__all__ = [
    "create_page",
    "get_active_page",
    "check_browser_alive",
    "close_resources",
    "find_page_by_title",
]
