from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_windows_installer_uses_orderly_shutdown_and_never_kills_processes():
    installer = (ROOT / "scripts" / "install_windows_update.ps1").read_text(encoding="utf-8")
    rollback = (ROOT / "scripts" / "rollback_windows_update.ps1").read_text(encoding="utf-8")

    for script in (installer, rollback):
        assert "/runtime/shutdown" in script
        assert "shutdown_requested" in script
        assert "No process was killed" in script
        assert "Stop-Process" not in script
        assert ".Kill()" not in script

    assert "Assert-ExpectedRuntimeOwner" in installer
    expected_bootstrap_path = "DGM-MAT" + chr(92) + "security" + chr(92) + "bootstrap.token"
    assert expected_bootstrap_path in installer
    assert expected_bootstrap_path in rollback
    assert "Assert-NoInstalledProcess -ExecutablePath $targetPath" in installer
    assert "Request-GracefulRuntimeShutdown -ExecutablePath $targetPath" in installer
