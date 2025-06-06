import builtins
from unittest import mock
import types
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    def goto(self, url, timeout=None):
        self.url = url
    def wait_for_url(self, *args, **kwargs):
        pass
    def wait_for_selector(self, *args, **kwargs):
        pass
    def fill(self, selector, value):
        pass
    def click(self, selector):
        pass
    def locator(self, selector):
        # mis conexiones visible only on first attempt
        if selector == MIS_CONEXIONES_TITLE_SELECTOR:
            return DummyLocator(self.attempt_ref[0] == 1)
        if selector == CERRAR_TODAS_SESIONES_SELECTOR:
            return DummyLocator(True)
        return DummyLocator(False)
    def wait_for_load_state(self, *args, **kwargs):
        pass
    def on(self, *args, **kwargs):
        pass
    def reload(self, *args, **kwargs):
        pass

class DummyContext:
    def __init__(self, attempt_ref):
        self.attempt_ref = attempt_ref
    def new_page(self):
        self.attempt_ref[0] += 1
        return DummyPage(self.attempt_ref)

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

def test_restart_after_closing_sessions(monkeypatch):
    attempt_ref = [0]

    dummy_playwright = DummyPlaywright(attempt_ref)
    monkeypatch.setattr(bot, "sync_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(bot, "analyze_har_and_extract_data", lambda *a, **k: None)
    monkeypatch.setattr(bot, "configure_run_specific_logging", lambda *a, **k: None)
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "")

    logger = mock.Mock()
    bot.run_automation(logger, max_attempts=2)

    # two attempts should have been performed: one for closing sessions and one for normal flow
    assert attempt_ref[0] == 2

