import pytest
from pathlib import Path
from core.workspace.workspace_manager import WorkspaceManager

def test_protection_rules_workflow(tmp_path):
    config = tmp_path / "protected_assets.yaml"
    config.write_text("protected_workflows:\n  - \".github/workflows/manual-repo-bootstrap.yml\"")

    wm = WorkspaceManager()
    wm.protected_config_path = config
    wm.protected_assets = wm._load_protected_assets()

    assert wm.is_protected(".github/workflows/manual-repo-bootstrap.yml") is True
    assert wm.is_protected(".github/workflows/auto.yml") is False

def test_protection_rules_manual_clones():
    wm = WorkspaceManager()
    assert wm.is_protected("C:/ProgramasGodMode/manual_clones/some_repo") is True
    assert wm.is_protected("manual_clones/another_repo") is True

def test_protection_rules_paths(tmp_path):
    config = tmp_path / "protected_assets.yaml"
    config.write_text("protected_paths:\n  - \"user_assets\"")

    wm = WorkspaceManager()
    wm.protected_config_path = config
    wm.protected_assets = wm._load_protected_assets()

    assert wm.is_protected("user_assets/photo.jpg") is True
    assert wm.is_protected("other/file.txt") is False
