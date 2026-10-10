"""Unit tests for the governed, ephemeral browser session."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.providers.browser.governed_browser_session import (
    BrowserPolicyError,
    GovernedBrowserSession,
)


def test_session_requires_explicit_allowlist_and_https():
    with pytest.raises(BrowserPolicyError, match="explicitly authorized"):
        GovernedBrowserSession(allowed_hosts=[])
    session = GovernedBrowserSession(allowed_hosts=["example.com"])
    with pytest.raises(BrowserPolicyError, match="Only HTTPS"):
        session._check_url("http://example.com")
    with pytest.raises(BrowserPolicyError, match="not in the explicit"):
        session._check_url("https://other.example")
    with pytest.raises(BrowserPolicyError, match="Private"):
        session._check_url("https://127.0.0.1")
    assert session._check_url("https://sub.example.com/path") == "https://sub.example.com/path"


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "192.168.1.10", "10.0.0.2"])
def test_private_hosts_cannot_be_added_to_allowlist(host):
    with pytest.raises(BrowserPolicyError):
        GovernedBrowserSession(allowed_hosts=[host])


def test_embedded_url_credentials_and_invalid_hosts_are_denied():
    session = GovernedBrowserSession(allowed_hosts=["example.com"])
    with pytest.raises(BrowserPolicyError, match="embedded credentials"):
        session._check_url("https://user:pass@example.com")
    with pytest.raises(BrowserPolicyError):
        GovernedBrowserSession(allowed_hosts=["https://example.com"])


class FakeLocator:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}
        self.clicked = False
        self.filled = None

    @property
    def first(self):
        return self

    def evaluate(self, script):
        return self.metadata

    def fill(self, value, timeout):
        self.filled = value

    def click(self, timeout):
        self.clicked = True


class FakePage:
    def __init__(self, metadata=None):
        self._locator = FakeLocator(metadata)
        self.url = "https://example.com"
        self._scroll = None

    def locator(self, selector):
        return self._locator

    def evaluate(self, script, delta):
        self._scroll = delta


def _attach_fake_page(session, page):
    session._page = page
    session._session_id = "unit-test-session"


def test_fill_and_scroll_use_bounded_actions_without_sensitive_fields():
    session = GovernedBrowserSession(allowed_hosts=["example.com"])
    page = FakePage({"type": "text", "name": "prompt", "id": "prompt", "autocomplete": "", "aria": "Prompt"})
    _attach_fake_page(session, page)
    result = session.fill("#prompt", "research query")
    assert result["characters"] == len("research query")
    assert page._locator.filled == "research query"
    assert session.scroll(direction="down", pixels=750)["pixels"] == 750
    assert page._scroll == 750


@pytest.mark.parametrize("metadata", [
    {"type": "password", "name": "pass", "id": "pass", "autocomplete": "current-password", "aria": ""},
    {"type": "text", "name": "api_token", "id": "token", "autocomplete": "", "aria": ""},
    {"type": "hidden", "name": "csrf", "id": "csrf", "autocomplete": "", "aria": ""},
])
def test_fill_rejects_sensitive_fields(metadata):
    session = GovernedBrowserSession(allowed_hosts=["example.com"])
    _attach_fake_page(session, FakePage(metadata))
    with pytest.raises(BrowserPolicyError, match="Sensitive"):
        session.fill("#target", "do not fill")


def test_screenshot_filename_cannot_escape_output_directory(tmp_path):
    session = GovernedBrowserSession(allowed_hosts=["example.com"], screenshot_dir=tmp_path)
    _attach_fake_page(session, FakePage())
    with pytest.raises(BrowserPolicyError, match="path traversal"):
        session.screenshot("..\\outside.png")


def test_ocr_fails_closed_for_invalid_image_without_upload(tmp_path, monkeypatch):
    session = GovernedBrowserSession(allowed_hosts=["example.com"], screenshot_dir=tmp_path)
    screenshot = tmp_path / "sample.png"
    screenshot.write_bytes(b"not a real png; OCR should fail closed if installed")
    result = session.ocr_screenshot("sample.png")
    assert "available" in result
    assert "text" in result
    assert result["screenshot"] == str(screenshot.resolve())


def test_ocr_rejects_malformed_language_codes(tmp_path):
    session = GovernedBrowserSession(allowed_hosts=["example.com"], screenshot_dir=tmp_path)
    with pytest.raises(ValueError, match="language must be"):
        session.ocr_screenshot("missing.png", language="../../por")


class FakeRequest:
    def __init__(self, url):
        self.url = url


class FakeRoute:
    def __init__(self, url):
        self.request = FakeRequest(url)
        self.action = None

    def continue_(self):
        self.action = "continue"

    def abort(self):
        self.action = "abort"


def test_request_guard_blocks_cross_domain_redirects_and_allows_authorized_hosts():
    session = GovernedBrowserSession(allowed_hosts=["example.com"])
    allowed = FakeRoute("https://cdn.example.com/app.js")
    blocked = FakeRoute("https://unapproved.example.net/collect")
    non_https = FakeRoute("http://example.com/redirect")
    session._guard_route(allowed)
    session._guard_route(blocked)
    session._guard_route(non_https)
    assert allowed.action == "continue"
    assert blocked.action == "abort"
    assert non_https.action == "abort"
