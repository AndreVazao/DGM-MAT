# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\api\\auth_middleware.py
"""Fail-closed authentication for inventoried HTTP and WebSocket API routes."""
from __future__ import annotations

import json
from typing import Any

from starlette.routing import Match
from starlette.types import ASGIApp, Receive, Scope, Send

from core.api.security_policy import SecurityScope, classify_route


_ALLOWED_ORIGINS = {
    "http://127.0.0.1:8181",
    "http://localhost:8181",
}


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            try:
                return value.decode("latin-1")
            except UnicodeDecodeError:
                return None
    return None


def _route_for_scope(scope: Scope, routes: list[Any]) -> tuple[Any | None, str]:
    for route in routes:
        try:
            match, _ = route.matches(scope)
        except Exception:
            continue
        if match is Match.FULL:
            return route, "websocket" if scope["type"] == "websocket" else "http"
    return None, "http"


def _required_scope(scope: SecurityScope) -> str | None:
    if scope is SecurityScope.PUBLIC_HEALTH:
        return None
    if scope in {SecurityScope.LOCAL_CLIENT, SecurityScope.LOCAL_STATIC_CLIENT, SecurityScope.LOCAL_DOCUMENTATION}:
        return "local-client"
    if scope in {SecurityScope.OPERATOR, SecurityScope.PROVIDER_API, SecurityScope.PROVIDER_OPERATOR}:
        return "operator"
    return "operator"


class LocalSessionAuthMiddleware:
    """Require a valid short-lived bearer session on every inventoried private route.

    The bootstrap exchange remains protected by its own loopback/origin/rate-limit
    checks. WebSocket credentials must be sent as an Authorization header, never
    in the query string. Unknown routes are left to FastAPI's normal 404 handling;
    known routes without a classification are denied.
    """

    def __init__(self, app: ASGIApp, *, routes: list[Any], session_manager: Any):
        self.app = app
        self.routes = routes
        self.session_manager = session_manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        route, route_type = _route_for_scope(scope, self.routes)
        if route is None:
            await self.app(scope, receive, send)
            return

        if route_type == "http":
            path = scope.get("path", "")
            method = scope.get("method", "GET").upper()
            if path == "/auth/session" and method == "POST":
                await self.app(scope, receive, send)
                return
            if method == "OPTIONS":
                origin = _header(scope, b"origin")
                if origin is not None and origin not in _ALLOWED_ORIGINS:
                    await self._http_error(send, 403, "Origin is not allowed.")
                    return
                await self.app(scope, receive, send)
                return
            classification = classify_route(
                getattr(route, "path", path),
                getattr(route, "methods", ()) or (),
                "mount" if route.__class__.__name__ == "Mount" else "http",
            )
            if classification is None:
                await self._http_error(send, 403, "Route has no security classification.")
                return
            if classification.scope is SecurityScope.PUBLIC_HEALTH:
                await self.app(scope, receive, send)
                return
            if classification.scope is SecurityScope.LOCAL_STATIC_CLIENT:
                # The static shell contains no credentials. All API data routes remain protected.
                await self.app(scope, receive, send)
                return
        else:
            classification = classify_route(getattr(route, "path", scope.get("path", "")), (), "websocket")
            if classification is None:
                await self._websocket_denied(send)
                return

        authorization = _header(scope, b"authorization")
        principal = None
        if isinstance(authorization, str):
            scheme, separator, token = authorization.partition(" ")
            if separator and scheme.casefold() == "bearer" and token and token.strip() == token and " " not in token and "\t" not in token:
                principal = self.session_manager.authenticate(token)

        if principal is None:
            if route_type == "websocket":
                await self._websocket_denied(send)
            else:
                await self._http_error(send, 401, "Valid local session required.")
            return

        required = _required_scope(classification.scope)
        if required and required not in principal.scopes:
            if route_type == "websocket":
                await self._websocket_denied(send, code=1008)
            else:
                await self._http_error(send, 403, "Session scope is insufficient.")
            return

        scope.setdefault("state", {})["dgm_principal"] = {
            "subject": principal.subject,
            "session_id": principal.session_id,
            "scopes": sorted(principal.scopes),
        }
        await self.app(scope, receive, send)

    @staticmethod
    async def _http_error(send: Send, status: int, detail: str) -> None:
        body = json.dumps({"detail": detail}, separators=(",", ":")).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode("ascii")), (b"cache-control", b"no-store")],
        })
        await send({"type": "http.response.body", "body": body})

    @staticmethod
    async def _websocket_denied(send: Send, code: int = 1008) -> None:
        await send({"type": "websocket.close", "code": code, "reason": "Authentication required"})
