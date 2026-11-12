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
        assert "Get-NetTCPConnection -LocalPort 8181 -State Listen" in script

    assert "Assert-ExpectedRuntimeOwner" in installer
    expected_bootstrap_path = "DGM-MAT" + chr(92) + "security" + chr(92) + "bootstrap.token"
    assert expected_bootstrap_path in installer
    assert expected_bootstrap_path in rollback
    assert "Wait-NoInstalledProcess -ExecutablePath $targetPath" in installer
    assert "Request-GracefulRuntimeShutdown -ExecutablePath $targetPath" in installer


def test_rollback_requires_manifest_sha256_for_previous_files():
    rollback = (ROOT / "scripts" / "rollback_windows_update.ps1").read_text(encoding="utf-8")
    assert "$manifest.previous_sha256" in rollback
    assert "$manifest.launcher_previous_sha256" in rollback
    assert "does not match the manifest SHA-256" in rollback


def test_rollback_validates_launcher_backup_before_replacing_executable():
    rollback = (ROOT / "scripts" / "rollback_windows_update.ps1").read_text(encoding="utf-8")
    launcher_preflight = rollback.index("$launcherBackupHash =")
    executable_replace = rollback.index('Move-Item -LiteralPath $restoreTemp -Destination $targetPath -Force')
    assert launcher_preflight < executable_replace
    assert "Previous launcher backup is missing; rollback refused before modifying the executable." in rollback


def test_rollback_stages_and_verifies_both_files_before_replacing_either():
    rollback = (ROOT / "scripts" / "rollback_windows_update.ps1").read_text(encoding="utf-8")
    exe_stage = rollback.index('Copy-Item -LiteralPath $backupPath -Destination $restoreTemp')
    exe_move = rollback.index('Move-Item -LiteralPath $restoreTemp -Destination $targetPath -Force')
    launcher_stage = rollback.index('Copy-Item -LiteralPath $launcherBackup -Destination $launcherRestoreTemp')
    launcher_move = rollback.index('Move-Item -LiteralPath $launcherRestoreTemp -Destination $launcherTarget -Force')
    assert exe_stage < exe_move
    assert launcher_stage < exe_move
    assert launcher_stage < launcher_move
    assert 'Rollback launcher staging copy failed manifest SHA-256 verification.' in rollback


def test_one_click_update_wrapper_uses_packaged_sha256_and_elevation_without_killing_processes():
    wrapper = (ROOT / "scripts" / "install_dgm_mat_update.ps1").read_text(encoding="utf-8")
    launcher = (ROOT / "Install-DGM-MAT-Update.bat").read_text(encoding="utf-8")

    assert 'DGM-MAT.exe.sha256' in wrapper
    assert '[a-f0-9]{64}' in wrapper
    assert 'ExpectedExeSha256 $expectedHash' in wrapper
    assert 'Start-Process -FilePath "powershell.exe" -Verb RunAs' in wrapper
    assert 'install_windows_update.ps1' in wrapper
    assert 'Stop-Process' not in wrapper
    assert 'Invoke-WebRequest' not in wrapper
    assert 'install_dgm_mat_update.ps1' in launcher
    assert 'ExecutionPolicy Bypass' in launcher
    assert 'did not complete' in launcher
