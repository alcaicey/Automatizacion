import builtins
from unittest import mock
import asyncio

import pytest

from src.scripts import bolsa_santiago_bot as bot
from src.config import MIS_CONEXIONES_TITLE_SELECTOR, CERRAR_TODAS_SESIONES_SELECTOR


class DummyLocator:
    def __init__(self, visible=True):
        self.visible = visible
    async def is_visible(self, timeout=0):
        return self.visible

    async def click(self):
        pass


class DummyPage:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
        self.url = bot.INITIAL_PAGE_URL
    async def goto(self, url, timeout=None, wait_until=None):
        self.url = url

    async def wait_for_url(self, *a, **k):
        pass

    async def wait_for_selector(self, *a, **k):
        pass

    async def fill(self, *a, **k):
        pass

    async def click(self, *a, **k):
        pass
    def content(self):
        return ""
    def locator(self, selector):
        if selector == MIS_CONEXIONES_TITLE_SELECTOR:
            return DummyLocator(False)
        if selector == CERRAR_TODAS_SESIONES_SELECTOR:
            return DummyLocator(True)
        return DummyLocator(False)
    async def wait_for_load_state(self, *a, **k):
        pass

    def on(self, *a, **k):
        pass

    async def reload(self, *a, **k):
        pass

    async def screenshot(self, *a, **k):
        pass
    def is_closed(self):
        return False


class DummyContext:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    async def new_page(self):
        self.attempt_ref[0] += 1
        return DummyPage(self.attempt_ref)

    async def close(self):
        pass

    async def cookies(self):
        return []


class DummyBrowser:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    async def new_context(self, **kwargs):
        return DummyContext(self.attempt_ref)

    async def close(self):
        pass


class DummyChromium:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    async def launch(self, **kwargs):
        return DummyBrowser(self.attempt_ref)


class DummyPlaywright:
    def __init__(self, attempt_ref):
        self.chromium = DummyChromium(attempt_ref)
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


def test_restart_when_json_empty(monkeypatch):
    attempt_ref = [0]
    dummy_playwright = DummyPlaywright(attempt_ref)
    monkeypatch.setattr(bot, "async_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(bot, "analyze_har_and_extract_data", lambda *a, **k: None)
    monkeypatch.setattr(bot, "configure_run_specific_logging", lambda *a, **k: None)
    monkeypatch.setenv("BOLSA_NON_INTERACTIVE", "1")
    monkeypatch.setattr(builtins, "input", lambda *a, **k: None)

    async def dummy_capture(*a, **k):
        return True, {"listaResult": []}, "ts"

    async def dummy_fetch(*a, **k):
        return True, {"listaResult": []}, "ts"

    monkeypatch.setattr(bot, "capture_premium_data_via_network", dummy_capture)
    monkeypatch.setattr(bot, "fetch_premium_data", dummy_fetch)

    logger = mock.Mock()
    asyncio.run(bot.run_automation(logger, max_attempts=2, keep_open=False))

    assert attempt_ref[0] >= 2
