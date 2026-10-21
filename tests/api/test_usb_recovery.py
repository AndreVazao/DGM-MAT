from pathlib import Path
from types import SimpleNamespace

from core.operator import usb_recovery


def test_parse_devices_keeps_authorization_state():
    parsed = usb_recovery.UsbRecoveryService._parse_devices(
        "List of devices attached\nABC123 device usb:1-2 product:demo\nXYZ offline\nNOPE unauthorized\n"
    )
    assert parsed == [
        {"serial": "ABC123", "state": "device", "details": "usb:1-2 product:demo"},
        {"serial": "XYZ", "state": "offline", "details": ""},
        {"serial": "NOPE", "state": "unauthorized", "details": ""},
    ]


def test_diagnose_fails_safely_when_adb_missing(monkeypatch):
    monkeypatch.setattr(usb_recovery, "_candidate_adb_paths", lambda: [])
    report = usb_recovery.UsbRecoveryService().diagnose()
    assert report["adb_found"] is False
    assert report["checks"][0]["status"] == "failed"
    assert report["destructive_actions_performed"] == []


def test_unknown_repair_action_never_executes_a_command(monkeypatch, tmp_path):
    adb = tmp_path / "adb.exe"
    adb.touch()
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(usb_recovery, "_candidate_adb_paths", lambda: [adb])
    result = usb_recovery.UsbRecoveryService(runner=runner).repair("shell-rm-data")
    assert result["status"] == "blocked"
    assert calls == []


def test_apk_install_requires_explicit_confirmation(monkeypatch, tmp_path):
    adb = tmp_path / "adb.exe"
    adb.touch()
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(usb_recovery, "_candidate_adb_paths", lambda: [adb])
    result = usb_recovery.UsbRecoveryService(runner=runner).repair("install-apk")
    assert result["status"] == "confirmation_required"
    assert calls == []



def test_usb_recovery_api_paths_have_explicit_security_classification():
    from core.api.security_policy import SecurityScope, classify_request_path

    assert classify_request_path("/mobile/usb-recovery/diagnose", "GET").scope is SecurityScope.OPERATOR
    assert classify_request_path("/mobile/usb-recovery/state", "GET").scope is SecurityScope.OPERATOR
    assert classify_request_path("/mobile/usb-recovery/repair", "POST").scope is SecurityScope.OPERATOR
    assert classify_request_path("/mobile/usb-recovery/repair", "GET") is None
    assert classify_request_path("/auth/pairing-code", "GET").scope is SecurityScope.OPERATOR
    assert classify_request_path("/auth/pair", "POST").scope is SecurityScope.OPERATOR



def test_pairing_code_is_one_time_and_issues_scoped_session(monkeypatch):
    from types import SimpleNamespace

    import pytest
    from fastapi import HTTPException, Response
    from core.api import local_auth_api

    monkeypatch.setattr(local_auth_api, "_attempts", {})
    pc_request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={},
    )
    response = Response()
    issued = local_auth_api.create_pairing_code(pc_request, response)
    assert response.headers["cache-control"] == "no-store"
    assert issued["expires_in"] == 300

    phone_request = SimpleNamespace(
        client=SimpleNamespace(host="100.64.0.2"),
        headers={"origin": "https://localhost"},
    )
    paired = local_auth_api.pair_mobile_client(
        local_auth_api.PairingRequest(
            code=issued["pairing_code"],
            client_id="dgm-mat-mobile-test",
        ),
        phone_request,
    )
    principal = local_auth_api.session_manager.authenticate(paired["access_token"])
    assert principal is not None
    assert "operator" in principal.scopes
    assert "local-client" in principal.scopes

    with pytest.raises(HTTPException) as error:
        local_auth_api.pair_mobile_client(
            local_auth_api.PairingRequest(
                code=issued["pairing_code"],
                client_id="dgm-mat-mobile-test",
            ),
            phone_request,
        )
    assert error.value.status_code == 401
