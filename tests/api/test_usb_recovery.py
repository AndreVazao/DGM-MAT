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
