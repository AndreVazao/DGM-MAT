from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from core.api import local_auth_api
from core.api import auth_middleware


def _request(origin: str):
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/auth/pair",
        "headers": [(b"origin", origin.encode("ascii"))],
        "client": ("127.0.0.1", 45678),
        "server": ("127.0.0.1", 8181),
        "scheme": "http",
    })


def test_extension_origin_is_allowed_only_for_explicit_valid_extension_id(monkeypatch):
    extension_id = "abcdefghijklmnopabcdefghijklmnop"
    monkeypatch.setenv("DGM_CHROME_EXTENSION_ID", extension_id)
    origin = "chrome-extension://" + extension_id
    assert origin in local_auth_api._allowed_origins()
    assert origin in auth_middleware._allowed_origins()
    local_auth_api._check_origin(_request(origin))


def test_unknown_or_malformed_extension_origins_are_rejected(monkeypatch):
    monkeypatch.setenv("DGM_CHROME_EXTENSION_ID", "not-a-valid-extension-id")
    with pytest.raises(HTTPException) as exc:
        local_auth_api._check_origin(_request("chrome-extension://abcdefghijklmnopabcdefghijklmnop"))
    assert exc.value.status_code == 403
    assert "chrome-extension://abcdefghijklmnopabcdefghijklmnop" not in local_auth_api._allowed_origins()


def test_extension_origin_configuration_does_not_enable_wildcard(monkeypatch):
    monkeypatch.setenv("DGM_CHROME_EXTENSION_ID", "*")
    assert not any(origin.startswith("chrome-extension://") for origin in local_auth_api._allowed_origins())


def test_extension_pairing_issues_eight_hour_browser_capture_only_session(monkeypatch):
    from fastapi import Response

    extension_id = "abcdefghijklmnopabcdefghijklmnop"
    origin = "chrome-extension://" + extension_id
    monkeypatch.setenv("DGM_CHROME_EXTENSION_ID", extension_id)
    monkeypatch.setattr(local_auth_api, "_attempts", {})
    request = _request(origin)
    response = Response()

    issued = local_auth_api.create_pairing_code(request, response)
    paired = local_auth_api.pair_mobile_client(
        local_auth_api.PairingRequest(
            code=issued["pairing_code"],
            client_id="dgm-mat-chrome-extension",
        ),
        request,
    )
    principal = local_auth_api.extension_session_manager.authenticate(paired["access_token"])
    assert principal is not None
    assert principal.scopes == frozenset({"browser-capture"})
    assert paired["expires_in"] == 8 * 60 * 60
    assert local_auth_api.session_manager.authenticate(paired["access_token"]) is None
