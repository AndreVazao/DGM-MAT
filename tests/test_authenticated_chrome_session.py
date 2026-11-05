from __future__ import annotations

import pytest

from core.providers.browser.authenticated_chrome_session import (
    AuthenticatedChromeError,
    AuthenticatedChromeSession,
)


@pytest.mark.parametrize("url", [
    "",
    "https://127.0.0.1:9222",
    "http://192.168.1.10:9222",
    "http://127.0.0.1",
    "http://user:pass@127.0.0.1:9222",
    "http://127.0.0.1:9222?token=x",
    "http://127.0.0.1:9222/devtools/browser/abc",
])
def test_cdp_endpoint_requires_explicit_loopback_http_without_credentials(url):
    with pytest.raises(AuthenticatedChromeError):
        AuthenticatedChromeSession(url)


def test_cdp_endpoint_accepts_explicit_loopback_port():
    session = AuthenticatedChromeSession("http://127.0.0.1:9222")
    assert session.cdp_url == "http://127.0.0.1:9222"


def test_provider_allowlist_rejects_non_provider_pages():
    session = AuthenticatedChromeSession("http://127.0.0.1:9222")
    assert session._check_provider_url("https://chatgpt.com/c/123")
    assert session._check_provider_url("https://gemini.google.com/app")
    assert session._check_provider_url("https://grok.com/") 
    with pytest.raises(AuthenticatedChromeError):
        session._check_provider_url("https://example.com/")
    with pytest.raises(AuthenticatedChromeError):
        session._check_provider_url("http://chatgpt.com/")


def test_custom_allowlist_is_explicit_and_narrow():
    session = AuthenticatedChromeSession(
        "http://localhost:9333", allowed_hosts=["chatgpt.com"]
    )
    assert session._check_provider_url("https://chatgpt.com/c/abc")
    with pytest.raises(AuthenticatedChromeError):
        session._check_provider_url("https://grok.com/")


def test_attach_requires_explicit_selection_when_multiple_provider_tabs_exist(monkeypatch):
    import sys
    import types

    class Locator:
        def inner_text(self, timeout):
            return "Visible conversation text"

    class Page:
        def __init__(self, url, title):
            self.url = url
            self._title = title
            self.timeout = None

        def is_closed(self):
            return False

        def title(self):
            return self._title

        def set_default_timeout(self, timeout):
            self.timeout = timeout

        def locator(self, selector):
            assert selector == "body"
            return Locator()

    first = Page("https://chatgpt.com/c/one", "ChatGPT conversation one")
    second = Page("https://gemini.google.com/app/two", "Gemini conversation two")

    class Context:
        pages = [first, second]

    class Browser:
        contexts = [Context()]

        def close(self):
            raise AssertionError("The user's Chrome browser must not be closed")

    browser = Browser()

    class Chromium:
        def connect_over_cdp(self, url, timeout):
            assert url == "http://127.0.0.1:9222"
            return browser

    class Playwright:
        chromium = Chromium()

        def __init__(self):
            self.stopped = False

        def stop(self):
            self.stopped = True

    playwright_instance = Playwright()
    api_module = types.ModuleType("playwright.sync_api")
    api_module.sync_playwright = lambda: types.SimpleNamespace(start=lambda: playwright_instance)
    package_module = types.ModuleType("playwright")
    package_module.sync_api = api_module
    monkeypatch.setitem(sys.modules, "playwright", package_module)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", api_module)

    session = AuthenticatedChromeSession("http://127.0.0.1:9222")
    attached = session.attach()
    assert attached["attached"] is True
    assert attached["selected"] is False
    assert len(attached["pages"]) == 2

    selected = session.select_page("https://gemini.google.com/app/two")
    assert selected["title"] == "Gemini conversation two"
    visible = session.read_visible_page()
    assert visible.text == "Visible conversation text"
    assert visible.truncated is False

    session.close()
    assert playwright_instance.stopped is True


def test_empty_provider_allowlist_is_rejected():
    with pytest.raises(AuthenticatedChromeError, match="At least one"):
        AuthenticatedChromeSession(
            "http://127.0.0.1:9222", allowed_hosts=[]
        )
