import builtins
import os
from unittest import mock
import asyncio

import pytest

from src.automatizacion_bolsa.config_loader import configure_run_specific_logging

from src.scripts import bolsa_santiago_bot as bot
from src.config import (
    MIS_CONEXIONES_TITLE_SELECTOR,
    CERRAR_TODAS_SESIONES_SELECTOR,
)

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
    async def goto(self, url, timeout=None):
        self.url = url

    async def wait_for_url(self, *args, **kwargs):
        pass

    async def wait_for_selector(self, *args, **kwargs):
        pass

    async def fill(self, selector, value):
        pass

    async def click(self, selector):
        pass
    def content(self):
        return ""
    def locator(self, selector):
        # mis conexiones visible only on first attempt
        if selector == MIS_CONEXIONES_TITLE_SELECTOR:
            return DummyLocator(self.attempt_ref[0] == 1)
        if selector == CERRAR_TODAS_SESIONES_SELECTOR:
            return DummyLocator(True)
        return DummyLocator(False)
    async def wait_for_load_state(self, *args, **kwargs):
        pass
    def on(self, *args, **kwargs):
        pass
    async def reload(self, *args, **kwargs):
        pass
    async def screenshot(self, *args, **kwargs):
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

def test_restart_after_closing_sessions(monkeypatch):
    attempt_ref = [0]

    dummy_playwright = DummyPlaywright(attempt_ref)
    monkeypatch.setattr(bot, "async_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(
        bot,
        "analyze_har_and_extract_data",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        bot,
        "configure_run_specific_logging",
        lambda *a, **k: None,
    )
    monkeypatch.setenv("BOLSA_NON_INTERACTIVE", "1")

    def forbid_input(*args, **kwargs):
        raise AssertionError("input should not be called")

    monkeypatch.setattr(builtins, "input", forbid_input)

    logger = mock.Mock()
    asyncio.run(bot.run_automation(logger, max_attempts=2, keep_open=False))

    # dos intentos principales deben haberse ejecutado. Tras los cambios el
    # script abre un contexto adicional al finalizar, por lo que el contador
    # puede ser mayor a 2.
    assert attempt_ref[0] >= 2


def test_keep_browser_alive_on_eof(monkeypatch):
    attempt_ref = [0]

    monkeypatch.delenv("BOLSA_NON_INTERACTIVE", raising=False)

    dummy_playwright = DummyPlaywright(attempt_ref)
    monkeypatch.setattr(bot, "async_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(
        bot,
        "analyze_har_and_extract_data",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        bot,
        "configure_run_specific_logging",
        lambda *a, **k: None,
    )

    def raise_eof(*args, **kwargs):
        raise EOFError()

    monkeypatch.setattr(builtins, "input", raise_eof)

    sleep_calls = []

    async def dummy_sleep(t):
        sleep_calls.append(t)
        if t == 60:
            raise RuntimeError("loop started")

    monkeypatch.setattr(bot.asyncio, "sleep", lambda t: dummy_sleep(t))

    logger = mock.Mock()
    with pytest.raises(RuntimeError, match="loop started"):
        asyncio.run(bot.run_automation(logger, max_attempts=1))

    assert 60 in sleep_calls


def test_no_sleep_when_keep_open_false(monkeypatch):
    attempt_ref = [0]
    monkeypatch.delenv("BOLSA_NON_INTERACTIVE", raising=False)
    dummy_playwright = DummyPlaywright(attempt_ref)
    monkeypatch.setattr(bot, "async_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(bot, "analyze_har_and_extract_data", lambda *a, **k: None)
    monkeypatch.setattr(bot, "configure_run_specific_logging", lambda *a, **k: None)
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "")
    sleep_calls = []

    async def record_sleep(t):
        sleep_calls.append(t)

    monkeypatch.setattr(bot.asyncio, "sleep", lambda t: record_sleep(t))
    logger = mock.Mock()
    asyncio.run(bot.run_automation(logger, max_attempts=1, keep_open=False))
    assert 60 not in sleep_calls
