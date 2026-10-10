# Path: C:\\ProgramasGodMode\\DGM-MAT\\cockpit\\api_client.py
"""Authenticated loopback HTTP client for the desktop cockpit.

Bootstrap and access tokens are held in process memory only. They are never
written to logs, settings, mission payloads or persistent storage.
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests


class LocalApiAuthenticationError(RuntimeError):
    """The desktop could not establish a protected local API session."""


_lock = threading.RLock()
_sessions: dict[str, tuple[str, float]] = {}
_SESSION_REFRESH_MARGIN_SECONDS = 20.0


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise LocalApiAuthenticationError("Only explicit HTTP(S) API URLs are supported.")
    if parsed.username or parsed.password:
        raise LocalApiAuthenticationError("Credentials are not allowed in API URLs.")
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def _bootstrap_path() -> Path:
    override = os.getenv("DGM_LOCAL_BOOTSTRAP_FILE")
    if override:
        return Path(override)
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        raise LocalApiAuthenticationError("Local bootstrap credential is not configured.")
    return Path(local_app_data) / "DGM-MAT" / "security" / "bootstrap.token"


def _read_bootstrap() -> str:
    try:
        token = _bootstrap_path().read_text(encoding="utf-8")
    except OSError as exc:
        raise LocalApiAuthenticationError("Local bootstrap credential is not configured.") from exc
    if not token or len(token) < 60 or token != token.strip():
        raise LocalApiAuthenticationError("Local bootstrap credential is invalid.")
    return token


def get_access_token(base_url: str, *, force_refresh: bool = False) -> str:
    origin = _origin(base_url)
    now = time.monotonic()
    with _lock:
        cached = _sessions.get(origin)
        if not force_refresh and cached and cached[1] - now > _SESSION_REFRESH_MARGIN_SECONDS:
            return cached[0]

    bootstrap = _read_bootstrap()
    try:
        response = requests.post(
            origin + "/auth/session",
            headers={"Authorization": "Bearer " + bootstrap},
            json={"client_id": "desktop-cockpit"},
            timeout=3.0,
        )
    except requests.RequestException as exc:
        raise LocalApiAuthenticationError("Could not reach the local session endpoint.") from exc
    finally:
        bootstrap = ""

    if response.status_code != 201:
        raise LocalApiAuthenticationError("Local session exchange was rejected.")
    try:
        payload = response.json()
        token = payload["access_token"]
        expires_in = int(payload["expires_in"])
        scopes = set(payload["scopes"])
    except (ValueError, TypeError, KeyError) as exc:
        raise LocalApiAuthenticationError("Local session response is invalid.") from exc
    if not isinstance(token, str) or len(token) < 40 or expires_in < 60 or "local-client" not in scopes or "operator" not in scopes:
        raise LocalApiAuthenticationError("Local session response failed validation.")

    with _lock:
        _sessions[origin] = (token, time.monotonic() + expires_in)
    return token


def authenticated_request(method: str, url: str, **kwargs):
    """Issue a local API request with a short-lived bearer session."""
    origin = _origin(url)
    supplied_headers = dict(kwargs.pop("headers", {}) or {})
    # A caller cannot override the session credential.
    supplied_headers.pop("Authorization", None)
    supplied_headers.pop("authorization", None)
    for attempt in range(2):
        token = get_access_token(origin, force_refresh=attempt == 1)
        headers = dict(supplied_headers)
        headers["Authorization"] = "Bearer " + token
        response = requests.request(method.upper(), url, headers=headers, **kwargs)
        if response.status_code != 401 or attempt == 1:
            return response
        with _lock:
            _sessions.pop(origin, None)
    return response


def clear_sessions() -> None:
    """Clear in-memory access tokens, primarily for shutdown and tests."""
    with _lock:
        _sessions.clear()
