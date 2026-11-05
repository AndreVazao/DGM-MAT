"""Attach to an explicitly enabled local Chrome UI without reading auth stores.

This adapter uses the normal rendered page only. It never inspects cookies,
storage, browser profile files, credentials or provider-private endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any


class AuthenticatedChromeError(RuntimeError):
    """The configured Chrome UI cannot be attached to safely."""


@dataclass(frozen=True)
class VisiblePage:
    url: str
    title: str
    text: str
    truncated: bool


class AuthenticatedChromeSession:
    """Read visible pages from a user-authorized Chrome CDP endpoint.

    The endpoint must be explicitly configured and bound to loopback. The
    session disconnects Playwright on close; it does not close the user's
    Chrome process or persist/export browser authentication state.
    """

    DEFAULT_PROVIDER_HOSTS = (
        "chatgpt.com",
        "chat.openai.com",
        "gemini.google.com",
        "grok.com",
        "x.com",
    )

    def __init__(
        self,
        cdp_url: str,
        *,
        allowed_hosts: tuple[str, ...] | list[str] | None = None,
        timeout_ms: int = 15000,
    ) -> None:
        self.cdp_url = self._validate_cdp_url(cdp_url)
        if not 1000 <= timeout_ms <= 60000:
            raise ValueError("timeout_ms must be between 1000 and 60000")
        hosts = self.DEFAULT_PROVIDER_HOSTS if allowed_hosts is None else allowed_hosts
        normalized = {self._normalize_host(host) for host in hosts}
        if not normalized:
            raise AuthenticatedChromeError("At least one provider host must be allowed")
        self.allowed_hosts = tuple(sorted(normalized))
        self.timeout_ms = timeout_ms
        self._playwright = None
        self._browser = None
        self._page = None

    @staticmethod
    def _normalize_host(host: str) -> str:
        value = str(host).strip().lower().rstrip(".")
        if not value or "://" in value or "/" in value or "@" in value:
            raise AuthenticatedChromeError("Invalid provider host")
        return value

    @staticmethod
    def _validate_cdp_url(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AuthenticatedChromeError(
                "An explicit loopback Chrome CDP URL is required"
            )
        parsed = urlparse(value.strip())
        if parsed.scheme != "http" or parsed.username or parsed.password:
            raise AuthenticatedChromeError(
                "Chrome CDP must use a local HTTP endpoint without embedded credentials"
            )
        host = (parsed.hostname or "").lower()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise AuthenticatedChromeError(
                "Chrome CDP endpoint must be bound to loopback only"
            )
        try:
            port = parsed.port
        except ValueError as exc:
            raise AuthenticatedChromeError("Invalid Chrome CDP port") from exc
        if port is None or not 1 <= port <= 65535:
            raise AuthenticatedChromeError("An explicit valid Chrome CDP port is required")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise AuthenticatedChromeError("Only the Chrome CDP root endpoint is allowed")
        return value.strip().rstrip("/")

    def _check_provider_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise AuthenticatedChromeError("Only HTTPS provider pages are readable")
        host = parsed.hostname.lower().rstrip(".")
        if not any(host == allowed or host.endswith("." + allowed)
                   for allowed in self.allowed_hosts):
            raise AuthenticatedChromeError(
                f"Page origin is outside the provider allowlist: {host}"
            )
        # x.com is a general social network; allow only the Grok UI route.
        if host == "x.com" or host.endswith(".x.com"):
            if not (parsed.path == "/i/grok" or parsed.path.startswith("/i/grok/")):
                raise AuthenticatedChromeError(
                    "Only the Grok interface path on x.com is allowed"
                )
        return url

    def attach(self) -> dict[str, Any]:
        if self._page is not None:
            return self.info()
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise AuthenticatedChromeError(
                "Playwright is not installed; authenticated Chrome capture is unavailable"
            ) from exc

        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.connect_over_cdp(
                self.cdp_url, timeout=self.timeout_ms
            )
            pages = [
                page
                for context in self._browser.contexts
                for page in context.pages
                if not page.is_closed()
            ]
            provider_pages = []
            for page in pages:
                try:
                    self._check_provider_url(page.url)
                except AuthenticatedChromeError:
                    continue
                provider_pages.append(page)
            if not provider_pages:
                self.close()
                raise AuthenticatedChromeError(
                    "No open page from an allowed provider was found in Chrome"
                )
            if len(provider_pages) == 1:
                self._page = provider_pages[0]
                self._page.set_default_timeout(self.timeout_ms)
            # With multiple provider tabs, retain the connection but require
            # explicit page selection; never guess which account/tab to read.
            return {
                "attached": True,
                "selected": self._page is not None,
                "pages": [
                    {"url": page.url, "title": page.title()}
                    for page in provider_pages
                ],
            }
        except AuthenticatedChromeError as exc:
            if self._browser is None:
                self.close()
            raise
        except Exception:
            self.close()
            raise

    def info(self) -> dict[str, Any]:
        if self._page is None:
            raise AuthenticatedChromeError("Chrome session is not attached")
        url = self._check_provider_url(self._page.url)
        return {"url": url, "title": self._page.title(), "attached": True}

    def list_provider_pages(self) -> list[dict[str, str]]:
        if self._browser is None:
            raise AuthenticatedChromeError("Chrome session is not attached")
        result = []
        for context in self._browser.contexts:
            for page in context.pages:
                if page.is_closed():
                    continue
                try:
                    url = self._check_provider_url(page.url)
                except AuthenticatedChromeError:
                    continue
                result.append({"url": url, "title": page.title()})
        return result

    def select_page(self, url: str) -> dict[str, Any]:
        if self._browser is None:
            raise AuthenticatedChromeError("Chrome session is not attached")
        target = self._check_provider_url(url)
        for context in self._browser.contexts:
            for page in context.pages:
                if not page.is_closed() and page.url == target:
                    self._page = page
                    self._page.set_default_timeout(self.timeout_ms)
                    return self.info()
        raise AuthenticatedChromeError("The requested provider page is not open")

    def navigate(self, url: str) -> dict[str, Any]:
        if self._page is None:
            raise AuthenticatedChromeError("Chrome session is not attached")
        checked = self._check_provider_url(url)
        response = self._page.goto(
            checked, wait_until="domcontentloaded", timeout=self.timeout_ms
        )
        return {
            "url": self._check_provider_url(self._page.url),
            "title": self._page.title(),
            "http_status": response.status if response is not None else None,
        }

    def read_visible_page(self, *, max_chars: int = 50000) -> VisiblePage:
        if not 100 <= max_chars <= 100000:
            raise ValueError("max_chars must be between 100 and 100000")
        if self._page is None:
            raise AuthenticatedChromeError("Chrome session is not attached")
        url = self._check_provider_url(self._page.url)
        text = self._page.locator("body").inner_text(timeout=self.timeout_ms)
        return VisiblePage(
            url=url,
            title=self._page.title(),
            text=text[:max_chars],
            truncated=len(text) > max_chars,
        )

    def close(self) -> None:
        """Disconnect the automation client without closing the user's Chrome."""
        self._page = None
        self._browser = None
        if self._playwright is not None:
            try:
                self._playwright.stop()
            finally:
                self._playwright = None
