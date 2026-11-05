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
