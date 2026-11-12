from pathlib import Path


def test_windows_update_backs_up_and_leaves_repository_learning_state_untouched():
    script = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "install_windows_update.ps1"
    ).read_text(encoding="utf-8")

    preserved = script.split("$preserved = @(", 1)[1].split("\n)", 1)[0]
    untouched = script.split("deliberately_untouched = @(", 1)[1].split("\n    )", 1)[0]

    assert 'storage\\cognition' in preserved
    assert 'data\\repository\\storage\\cognition' in preserved
    assert 'storage\\cognition' in untouched


def test_windows_update_backs_up_and_leaves_persistent_vault_untouched():
    script = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "install_windows_update.ps1"
    ).read_text(encoding="utf-8")

    preserved = script.split("$preserved = @(", 1)[1].split("\n)", 1)[0]
    untouched = script.split("deliberately_untouched = @(", 1)[1].split("\n    )", 1)[0]

    assert 'Join-Path $localDgmRoot "Vault"' in preserved
    assert 'data\\localappdata\\DGM-MAT\\Vault' in preserved
    assert 'Join-Path $localDgmRoot "Vault"' in untouched
    assert "Vault" in script
