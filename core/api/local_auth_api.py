# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\api\\local_auth_api.py
"""Loopback-only bootstrap-to-session endpoint; existing routes are not yet enforced."""
from __future__ import annotations

import hmac
import os
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, constr

from core.api.local_sessions import LocalSessionManager

router = APIRouter(prefix="/auth", tags=["local-auth"])
session_manager = LocalSessionManager(ttl_seconds=1800)
_lock = threading.Lock()
_attempts: dict[str, list[float]] = {}
_RATE_WINDOW_SECONDS = 60.0
_MAX_ATTEMPTS_PER_WINDOW = 8
_ALLOWED_ORIGINS = {
    "http://127.0.0.1:8181",
    "http://localhost:8181",
}


class SessionRequest(BaseModel):
    client_id: constr(strip_whitespace=True, min_length=1, max_length=64)

    model_config = ConfigDict(extra="forbid")


def _bootstrap_path() -> Path:
    override = os.getenv("DGM_LOCAL_BOOTSTRAP_FILE")
    if override:
        return Path(override)
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        raise HTTPException(status_code=503, detail="Local bootstrap credential is not configured.")
    return Path(local_app_data) / "DGM-MAT" / "security" / "bootstrap.token"


def _read_bootstrap_token() -> str:
    try:
        token = _bootstrap_path().read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(status_code=503, detail="Local bootstrap credential is not configured.")
    if not token or len(token) < 60 or token != token.strip():
        raise HTTPException(status_code=503, detail="Local bootstrap credential is invalid.")
    return token


def _is_loopback(request: Request) -> bool:
    client = request.client
    if client is None:
        return False
    host = client.host.strip("[]").casefold()
    return host == "localhost" or host == "127.0.0.1" or host == "::1"


def _check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin not in _ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin is not allowed for local pairing.")


def _rate_limit(client_key: str) -> None:
    now = time.monotonic()
    with _lock:
        recent = [stamp for stamp in _attempts.get(client_key, []) if now - stamp < _RATE_WINDOW_SECONDS]
        if len(recent) >= _MAX_ATTEMPTS_PER_WINDOW:
            _attempts[client_key] = recent
            raise HTTPException(status_code=429, detail="Too many local session attempts.")
        recent.append(now)
        _attempts[client_key] = recent


@router.post("/session", status_code=201)
def create_local_session(
    payload: SessionRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Exchange a protected PC-local bootstrap secret for a short-lived session."""
    if not _is_loopback(request):
        raise HTTPException(status_code=403, detail="Local session issuance is loopback-only.")
    _check_origin(request)
    client_key = request.client.host if request.client else "unknown"
    _rate_limit(client_key)
    expected = _read_bootstrap_token()
    if not isinstance(authorization, str):
        raise HTTPException(status_code=401, detail="Bootstrap bearer credential required.")
    scheme, separator, supplied = authorization.partition(" ")
    if not separator or scheme.casefold() != "bearer" or not supplied or supplied.strip() != supplied:
        raise HTTPException(status_code=401, detail="Bootstrap bearer credential required.")
    if not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid bootstrap credential.")

    # Scope is chosen by server policy, never supplied by the caller.
    token, principal = session_manager.create_session(
        subject=payload.client_id,
        scopes={"local-client", "operator"},
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": int(principal.expires_at - principal.issued_at),
        "expires_at": principal.expires_at,
        "session_id": principal.session_id,
        "scopes": sorted(principal.scopes),
    }
