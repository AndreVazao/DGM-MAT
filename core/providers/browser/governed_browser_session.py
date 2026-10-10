"""Governed browser session for public web research and user-authorized free web UIs.

This service deliberately keeps Playwright contexts in memory, does not persist
cookies/storage state, does not fill credential fields, and never bypasses
CAPTCHA, MFA, paywalls, or provider limits.
"""
from __future__ import annotations

import ipaddress
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class BrowserPolicyError(ValueError):
    """Raised when a browser action crosses the explicit session policy."""


@dataclass(frozen=True)
class BrowserSessionInfo:
    session_id: str
    current_url: str
    title: str
    headed: bool
    allowed_hosts: tuple[str, ...]


class GovernedBrowserSession:
    """A bounded Playwright session. One instance owns one ephemeral browser context."""

    _SENSITIVE_SELECTOR = re.compile(
        r"password|passwd|secret|token|api.?key|credit.?card|cvv|otp|one.?time|"
        r"authenticator|recovery.?code|\bpin\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        *,
        allowed_hosts: list[str],
        headed: bool = True,
        timeout_ms: int = 15000,
        screenshot_dir: str | Path | None = None,
    ) -> None:
        if not allowed_hosts:
            raise BrowserPolicyError("At least one explicitly authorized host is required")
        if not 1000 <= timeout_ms <= 60000:
            raise ValueError("timeout_ms must be between 1000 and 60000")
        normalized = {self._normalize_host(host) for host in allowed_hosts}
        self.allowed_hosts = tuple(sorted(normalized))
        self.headed = bool(headed)
        self.timeout_ms = timeout_ms
        self.screenshot_dir = Path(screenshot_dir).resolve() if screenshot_dir else None
        if self.screenshot_dir:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._session_id: str | None = None
        self._lock = threading.RLock()

    @staticmethod
    def _normalize_host(host: str) -> str:
        value = host.strip().lower().rstrip(".")
        if not value or "://" in value or "/" in value or "@" in value:
            raise BrowserPolicyError(f"Invalid host entry: {host!r}")
        if value in {"localhost", "localhost.localdomain"}:
            raise BrowserPolicyError("Loopback hosts are not allowed by the default web research policy")
        try:
            address = ipaddress.ip_address(value.strip("[]"))
        except ValueError:
            address = None
        if address is not None and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
            raise BrowserPolicyError("Private, loopback, link-local and reserved IP addresses are denied")
        return value

    def _check_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise BrowserPolicyError("Only HTTPS web pages are allowed by this session")
        if not parsed.hostname or parsed.username or parsed.password:
            raise BrowserPolicyError("URL must have a host and must not contain embedded credentials")
        host = parsed.hostname.lower().rstrip(".")
        try:
            address = ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            address = None
        if address is not None and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
            raise BrowserPolicyError("Private, loopback, link-local and reserved IP addresses are denied")
        if not any(host == allowed or host.endswith("." + allowed) for allowed in self.allowed_hosts):
            raise BrowserPolicyError(f"Host {host!r} is not in the explicit session allowlist")
        return url

    def start(self) -> BrowserSessionInfo:
        with self._lock:
            if self._page is not None:
                return self.info()
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as exc:
                raise RuntimeError("Playwright is not installed; browser capability remains unavailable") from exc
            import uuid
            self._playwright = sync_playwright().start()
            try:
                launch_options: dict[str, Any] = {"headless": not self.headed, "args": ["--disable-gpu"]}
                # Prefer an already installed browser to avoid downloading a second browser bundle.
                browser_candidates = (
                    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
                    Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
                    Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
                    Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                )
                installed_browser = next((candidate for candidate in browser_candidates if candidate.is_file()), None)
                if installed_browser is not None:
                    launch_options["executable_path"] = str(installed_browser)
                self._browser = self._playwright.chromium.launch(**launch_options)
                # Non-persistent context: cookies and storage state are not exported or saved.
                self._context = self._browser.new_context(accept_downloads=False)
                self._context.set_default_timeout(self.timeout_ms)
                # Enforce the allowlist on every request, including redirects and subresources.
                self._context.route("**/*", self._guard_route)
                self._page = self._context.new_page()
                self._session_id = uuid.uuid4().hex
                return self.info()
            except Exception:
                self.close()
                raise

    def _guard_route(self, route) -> None:
        url = route.request.url
        if url.startswith(("data:", "blob:", "about:")):
            route.continue_()
            return
        try:
            self._check_url(url)
        except BrowserPolicyError:
            route.abort()
            return
        route.continue_()

    def _require_page(self):
        if self._page is None:
            raise RuntimeError("Browser session is not started")
        return self._page

    def navigate(self, url: str) -> dict[str, Any]:
        with self._lock:
            page = self._require_page()
            checked = self._check_url(url)
            response = page.goto(checked, wait_until="domcontentloaded", timeout=self.timeout_ms)
            return {
                "url": page.url,
                "title": page.title(),
                "http_status": response.status if response is not None else None,
                "navigation_completed": True,
            }

    def read_page(self, *, max_chars: int = 20000) -> dict[str, Any]:
        if not 100 <= max_chars <= 50000:
            raise ValueError("max_chars must be between 100 and 50000")
        with self._lock:
            page = self._require_page()
            text = page.locator("body").inner_text(timeout=self.timeout_ms)
            return {"url": page.url, "title": page.title(), "text": text[:max_chars], "truncated": len(text) > max_chars}

    def click(self, selector: str) -> dict[str, Any]:
        with self._lock:
            page = self._require_page()
            self._validate_selector(selector)
            locator = page.locator(selector).first
            locator.click(timeout=self.timeout_ms)
            return {"action": "click", "selector": selector, "url": page.url}

    def fill(self, selector: str, value: str) -> dict[str, Any]:
        with self._lock:
            page = self._require_page()
            self._validate_selector(selector)
            if not isinstance(value, str) or len(value) > 12000:
                raise ValueError("Input must be text no longer than 12000 characters")
            locator = page.locator(selector).first
            try:
                metadata = locator.evaluate("""el => ({
                    type: (el.getAttribute('type') || '').toLowerCase(),
                    name: el.getAttribute('name') || '',
                    id: el.id || '',
                    autocomplete: el.getAttribute('autocomplete') || '',
                    aria: el.getAttribute('aria-label') || ''
                })""")
            except Exception as exc:
                raise BrowserPolicyError("Could not inspect target field; refusing to fill") from exc
            fingerprint = " ".join(str(v) for v in metadata.values())
            if metadata.get("type") in {"password", "file", "hidden"} or self._SENSITIVE_SELECTOR.search(fingerprint):
                raise BrowserPolicyError("Sensitive/credential fields cannot be filled by this service")
            locator.fill(value, timeout=self.timeout_ms)
            return {"action": "fill", "selector": selector, "characters": len(value), "url": page.url}

    @staticmethod
    def _validate_selector(selector: str) -> None:
        if not isinstance(selector, str) or not selector.strip() or len(selector) > 500:
            raise ValueError("A non-empty selector of at most 500 characters is required")

    def scroll(self, *, direction: str = "down", pixels: int = 600) -> dict[str, Any]:
        if direction not in {"up", "down"} or not 1 <= pixels <= 3000:
            raise ValueError("direction must be up/down and pixels must be between 1 and 3000")
        with self._lock:
            page = self._require_page()
            delta = pixels if direction == "down" else -pixels
            page.evaluate("(delta) => window.scrollBy(0, delta)", delta)
            return {"action": "scroll", "direction": direction, "pixels": pixels, "url": page.url}

    def screenshot(self, filename: str) -> dict[str, Any]:
        with self._lock:
            page = self._require_page()
            if self.screenshot_dir is None:
                raise RuntimeError("Screenshot output directory was not configured")
            if not isinstance(filename, str) or Path(filename).name != filename:
                raise BrowserPolicyError("Screenshot path traversal denied")
            name = Path(filename).name
            if not name or name in {".", ".."}:
                raise ValueError("A simple screenshot filename is required")
            if not name.lower().endswith(".png"):
                name += ".png"
            target = (self.screenshot_dir / name).resolve()
            if target.parent != self.screenshot_dir:
                raise BrowserPolicyError("Screenshot path traversal denied")
            page.screenshot(path=str(target), full_page=False)
            return {"path": str(target), "url": page.url, "format": "png"}

    def ocr_screenshot(self, filename: str, *, language: str = "por+eng") -> dict[str, Any]:
        """Run local OCR only; never installs packages or uploads images."""
        parts = language.split("+") if isinstance(language, str) else []
        if not 1 <= len(parts) <= 5 or any(not re.fullmatch(r"[a-z]{3}", part) for part in parts):
            raise ValueError("language must be a Tesseract language code or short combination, e.g. por+eng")
        if self.screenshot_dir is None:
            raise RuntimeError("Screenshot output directory was not configured")
        target = (self.screenshot_dir / Path(filename).name).resolve()
        if target.parent != self.screenshot_dir or not target.is_file():
            raise ValueError("Screenshot must exist inside the configured screenshot directory")
        binary = shutil.which("tesseract")
        if not binary:
            candidate = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
            if candidate.is_file():
                binary = str(candidate)
        if not binary:
            return {"available": False, "text": "", "reason": "Tesseract executable was not found.", "screenshot": str(target)}
        try:
            result = subprocess.run(
                [binary, str(target), "stdout", "-l", language],
                capture_output=True, text=True, timeout=30, shell=False, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "available": False, "text": "",
                "reason": f"OCR engine unavailable or failed: {type(exc).__name__}",
                "screenshot": str(target),
            }
        if result.returncode != 0:
            return {
                "available": False, "text": "",
                "reason": "Tesseract returned a non-zero exit code; verify the requested language data.",
                "screenshot": str(target),
            }
        return {"available": True, "text": result.stdout[:20000], "screenshot": str(target)}

    def info(self) -> BrowserSessionInfo:
        page = self._require_page()
        return BrowserSessionInfo(
            session_id=self._session_id or "",
            current_url=page.url,
            title=page.title(),
            headed=self.headed,
            allowed_hosts=self.allowed_hosts,
        )

    def close(self) -> None:
        with self._lock:
            for resource in (self._context, self._browser):
                try:
                    if resource is not None:
                        resource.close()
                except Exception:
                    pass
            try:
                if self._playwright is not None:
                    self._playwright.stop()
            except Exception:
                pass
            self._page = self._context = self._browser = self._playwright = None
            self._session_id = None
