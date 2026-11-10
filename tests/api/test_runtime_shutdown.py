from __future__ import annotations

import asyncio

import pytest
from fastapi import BackgroundTasks
from fastapi import HTTPException
from starlette.requests import Request

from core.api.runtime_api import request_runtime_shutdown_endpoint


def _request(host: str, scopes: list[str] | None = None) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/runtime/shutdown",
        "headers": [],
        "client": (host, 43210),
        "server": ("127.0.0.1", 8181),
        "scheme": "http",
        "state": {
            "dgm_principal": {
                "session_id": "test-session",
                "scopes": scopes if scopes is not None else ["operator"],
            }
        },
    })


def test_runtime_shutdown_requires_loopback_operator_and_signals_both_layers(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "core.api.api_server.request_api_shutdown",
        lambda: calls.append("api") or True,
    )
    monkeypatch.setattr(
        "core.runtime.runtime_control.request_runtime_shutdown",
        lambda: calls.append("runtime"),
    )

    background_tasks = BackgroundTasks()
    result = request_runtime_shutdown_endpoint(_request("127.0.0.1"), background_tasks)

    assert calls == ["api"]
    asyncio.run(background_tasks())
    assert calls == ["api", "runtime"]
    assert result == {
        "status": "shutdown_requested",
        "service": "dgm-mat",
        "provider_contacted": False,
    }


def test_runtime_shutdown_rejects_non_loopback_before_signalling(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "core.api.api_server.request_api_shutdown",
        lambda: calls.append("api") or True,
    )
    monkeypatch.setattr(
        "core.runtime.runtime_control.request_runtime_shutdown",
        lambda: calls.append("runtime"),
    )

    with pytest.raises(HTTPException) as exc:
        request_runtime_shutdown_endpoint(_request("192.0.2.20"), BackgroundTasks())

    assert exc.value.status_code == 403
    assert calls == []


def test_runtime_shutdown_requires_operator_scope(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "core.api.api_server.request_api_shutdown",
        lambda: calls.append("api") or True,
    )
    monkeypatch.setattr(
        "core.runtime.runtime_control.request_runtime_shutdown",
        lambda: calls.append("runtime"),
    )

    with pytest.raises(HTTPException) as exc:
        request_runtime_shutdown_endpoint(_request("127.0.0.1", ["local-client"]), BackgroundTasks())

    assert exc.value.status_code == 403
    assert calls == []


def test_runtime_shutdown_fails_closed_when_server_control_is_unavailable(monkeypatch):
    calls = []
    monkeypatch.setattr("core.api.api_server.request_api_shutdown", lambda: False)
    monkeypatch.setattr(
        "core.runtime.runtime_control.request_runtime_shutdown",
        lambda: calls.append("runtime"),
    )

    with pytest.raises(HTTPException) as exc:
        request_runtime_shutdown_endpoint(_request("127.0.0.1"), BackgroundTasks())

    assert exc.value.status_code == 503
    assert calls == []


def test_api_server_shutdown_request_sets_uvicorn_exit_flag(monkeypatch):
    from core.api import api_server

    class FakeServer:
        should_exit = False

    server = FakeServer()
    monkeypatch.setattr(api_server, "_api_server", server)

    assert api_server.request_api_shutdown() is True
    assert server.should_exit is True


def test_api_server_shutdown_request_fails_when_server_is_not_running(monkeypatch):
    from core.api import api_server

    monkeypatch.setattr(api_server, "_api_server", None)
    assert api_server.request_api_shutdown() is False
