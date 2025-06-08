import builtins
from unittest import mock

import pytest

from src.scripts import bolsa_santiago_bot as bot

# Dummy objects for Playwright simulation
class DummyLocator:
    def __init__(self, visible=False):
        self.visible = visible
    def is_visible(self, timeout=0):
        return self.visible
    def click(self):
        pass

class DummyPage:
    def __init__(self):
        self.url = bot.INITIAL_PAGE_URL
        self.wait_for_function_calls = []
    def goto(self, url, timeout=None):
        self.url = url
    def wait_for_url(self, *a, **k):
        pass
    def wait_for_selector(self, *a, **k):
        pass
    def fill(self, selector, value):
        pass
    def click(self, selector):
        # Simulate redirection to captcha page after login
        self.url = "https://radware.example.com/captcha"
    def content(self):
        return "captcha page"
    def wait_for_function(self, js, timeout=0):
        self.wait_for_function_calls.append((js, timeout))
    def locator(self, selector):
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
    def __init__(self, page):
        self.page = page
    def new_page(self):
        return self.page
    def close(self):
        pass

class DummyBrowser:
    def __init__(self, page):
        self.page = page
    def new_context(self, **kwargs):
        return DummyContext(self.page)
    def close(self):
        pass

class DummyChromium:
    def __init__(self, page):
        self.page = page
    def launch(self, **kwargs):
        return DummyBrowser(self.page)

class DummyPlaywright:
    def __init__(self, page):
        self.chromium = DummyChromium(page)
    def start(self):
        return self


def test_wait_on_captcha(monkeypatch):
    page = DummyPage()
    dummy_playwright = DummyPlaywright(page)

    monkeypatch.setattr(bot, "sync_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(bot, "analyze_har_and_extract_data", lambda *a, **k: None)
    monkeypatch.setattr(bot, "configure_run_specific_logging", lambda *a, **k: None)
    sleep_calls = []
    def dummy_sleep(t):
        sleep_calls.append(t)
    monkeypatch.setattr(bot.time, "sleep", dummy_sleep)
    monkeypatch.setattr(bot.random, "uniform", lambda a, b: a)
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "")

    logger = mock.Mock()
    bot.run_automation(logger, max_attempts=1, non_interactive=False, keep_open=False)

    assert 10 in sleep_calls
