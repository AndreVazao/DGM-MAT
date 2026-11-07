from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_windows_installer_requires_independent_executable_digest_before_mutation():
    script = (ROOT / "scripts" / "install_windows_update.ps1").read_text(
        encoding="utf-8"
    )

    digest_parameter = script.index("[string]$ExpectedExeSha256")
    digest_validation = script.index("$packageHash = (Get-FileHash")
    backup_root_creation = script.index(
        'New-Item -ItemType Directory -Path $BackupRoot -Force'
    )
    runtime_stop = script.index("Stop-ExactInstalledProcess -ExecutablePath")

    assert digest_parameter < digest_validation < backup_root_creation
    assert digest_validation < runtime_stop
    assert "^[A-Fa-f0-9]{64}$" in script
    assert "[StringComparison]::OrdinalIgnoreCase" in script
    assert "No installation changes were made" in script
    assert "package_sha256_verified_before_mutation = $true" in script


def test_windows_build_publishes_executable_digest_as_separate_artifact_file():
    workflow = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(
        encoding="utf-8"
    )

    assert 'publish\\DGM-MAT.exe.sha256' in workflow
    assert '"$exeHash  DGM-MAT.exe"' in workflow
    assert "Executable SHA-256 sidecar missing or malformed" in workflow
