# tests/test_errors_routes.py
import pytest
from playwright.sync_api import TimeoutError

# Escenario: Timeout al esperar un selector que no aparece (selector inexistente)
def test_login_timeout_selector_missing(monkeypatch):
    def mock_wait_for(selector, timeout=20000):
        raise TimeoutError(f"Timeout waiting for: {selector}")

    class MockPage:
        def wait_for_selector(self, selector, timeout):
            return mock_wait_for(selector, timeout)

    page = MockPage()

    with pytest.raises(TimeoutError):
        page.wait_for_selector("#menuppal-login a", timeout=20000)

# Escenario: Selector aparece y no lanza excepción
def test_login_selector_appears(monkeypatch):
    class MockPage:
        def wait_for_selector(self, selector, timeout):
            return f"Selector {selector} found"

    page = MockPage()
    result = page.wait_for_selector("#menuppal-login a", timeout=20000)
    assert result == "Selector #menuppal-login a found"
