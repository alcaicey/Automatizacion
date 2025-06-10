import builtins
from unittest import mock

import pytest

from src.scripts import bolsa_santiago_bot as bot
from src.config import MIS_CONEXIONES_TITLE_SELECTOR, CERRAR_TODAS_SESIONES_SELECTOR


class DummyLocator:
    def __init__(self, visible=True):
        self.visible = visible
    def is_visible(self, timeout=0):
        return self.visible
    def click(self):
        pass


class DummyPage:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
        self.url = bot.INITIAL_PAGE_URL
    def goto(self, url, timeout=None, wait_until=None):
        self.url = url
    def wait_for_url(self, *a, **k):
        pass
    def wait_for_selector(self, *a, **k):
        pass
    def fill(self, *a, **k):
        pass
    def click(self, *a, **k):
        pass
    def content(self):
        return ""
    def locator(self, selector):
        if selector == MIS_CONEXIONES_TITLE_SELECTOR:
            return DummyLocator(False)
        if selector == CERRAR_TODAS_SESIONES_SELECTOR:
            return DummyLocator(True)
        return DummyLocator(False)
    def wait_for_load_state(self, *a, **k):
        pass
    def on(self, *a, **k):
        pass
    def reload(self, *a, **k):
        pass
    def screenshot(self, *a, **k):
        pass
    def is_closed(self):
        return False


class DummyContext:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    def new_page(self):
        self.attempt_ref[0] += 1
        return DummyPage(self.attempt_ref)
    def close(self):
        pass
    def cookies(self):
        return []


class DummyBrowser:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    def new_context(self, **kwargs):
        return DummyContext(self.attempt_ref)
    def close(self):
        pass


class DummyChromium:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    def launch(self, **kwargs):
        return DummyBrowser(self.attempt_ref)


class DummyPlaywright:
    def __init__(self, attempt_ref):
        self.chromium = DummyChromium(attempt_ref)
    def start(self):
        return self


def test_restart_when_json_empty(monkeypatch):
    attempt_ref = [0]
    dummy_playwright = DummyPlaywright(attempt_ref)
    monkeypatch.setattr(bot, "sync_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(bot, "analyze_har_and_extract_data", lambda *a, **k: None)
    monkeypatch.setattr(bot, "configure_run_specific_logging", lambda *a, **k: None)
    monkeypatch.setenv("BOLSA_NON_INTERACTIVE", "1")
    monkeypatch.setattr(builtins, "input", lambda *a, **k: None)

    monkeypatch.setattr(
        bot,
        "capture_premium_data_via_network",
        lambda *a, **k: (True, {"listaResult": []}, "ts"),
    )
    monkeypatch.setattr(
        bot,
        "fetch_premium_data",
        lambda *a, **k: (True, {"listaResult": []}, "ts"),
    )

    logger = mock.Mock()
    bot.run_automation(logger, max_attempts=2, keep_open=False)

    assert attempt_ref[0] >= 2
