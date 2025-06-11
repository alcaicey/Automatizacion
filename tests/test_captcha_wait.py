import builtins
from unittest import mock
import asyncio

import pytest

from src.scripts import bolsa_santiago_bot as bot

# Dummy objects for Playwright simulation
class DummyLocator:
    def __init__(self, visible=False):
        self.visible = visible

    async def is_visible(self, timeout=0):
        return self.visible

    async def click(self):
        pass

class DummyPage:
    def __init__(self):
        self.url = bot.INITIAL_PAGE_URL
        self.wait_for_function_calls = []
    async def goto(self, url, timeout=None):
        self.url = url

    async def wait_for_url(self, *a, **k):
        pass

    async def wait_for_selector(self, *a, **k):
        pass

    async def fill(self, selector, value):
        pass

    async def click(self, selector):
        # Simulate redirection to captcha page after login
        self.url = "https://radware.example.com/captcha"

    def content(self):
        return "captcha page"

    async def wait_for_function(self, js, timeout=0):
        self.wait_for_function_calls.append((js, timeout))

    def locator(self, selector):
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
    def __init__(self, page):
        self.page = page
    async def new_page(self):
        return self.page

    async def close(self):
        pass

class DummyBrowser:
    def __init__(self, page):
        self.page = page
    async def new_context(self, **kwargs):
        return DummyContext(self.page)

    async def close(self):
        pass

class DummyChromium:
    def __init__(self, page):
        self.page = page
    async def launch(self, **kwargs):
        return DummyBrowser(self.page)

class DummyPlaywright:
    def __init__(self, page):
        self.chromium = DummyChromium(page)
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


def test_wait_on_captcha(monkeypatch):
    page = DummyPage()
    dummy_playwright = DummyPlaywright(page)

    monkeypatch.setattr(bot, "async_playwright", lambda: dummy_playwright)
    monkeypatch.setattr(bot, "analyze_har_and_extract_data", lambda *a, **k: None)
    monkeypatch.setattr(bot, "configure_run_specific_logging", lambda *a, **k: None)
    sleep_calls = []
    async def dummy_sleep(t):
        sleep_calls.append(t)
    monkeypatch.setattr(bot.asyncio, "sleep", lambda t: dummy_sleep(t))
    monkeypatch.setattr(bot.random, "uniform", lambda a, b: a)
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "")

    logger = mock.Mock()
    asyncio.run(bot.run_automation(logger, max_attempts=1, non_interactive=False, keep_open=False))

    assert 10 in sleep_calls
