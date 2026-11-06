import os
import shutil
import sys
from pathlib import Path
import pytest
from core.storage.storage_manager import RuntimeStorageManager

@pytest.fixture
def temp_storage_dir(tmp_path):
    storage_dir = tmp_path / "dgm_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir

def test_storage_manager_default_path(monkeypatch, tmp_path):
    """Default runtime data is per-user and independent of the executable."""
    monkeypatch.delenv("DGM_STORAGE_PATH", raising=False)
    monkeypatch.delenv("DGM_BASE_PATH", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    manager = RuntimeStorageManager()
    expected = tmp_path / "AppData" / "Local" / "DGM-MAT" / "Vault" / "runtime"
    assert manager.base_path == expected.resolve()
    assert (expected / "missions").is_dir()

def test_storage_manager_env_override(temp_storage_dir):
    os.environ["DGM_STORAGE_PATH"] = str(temp_storage_dir)
    try:
        manager = RuntimeStorageManager()
        assert manager.base_path == temp_storage_dir.resolve()
        assert (temp_storage_dir / "memory").exists()
    finally:
        del os.environ["DGM_STORAGE_PATH"]

def test_storage_manager_base_path_override(temp_storage_dir):
    os.environ["DGM_BASE_PATH"] = str(temp_storage_dir)
    try:
        manager = RuntimeStorageManager()
        expected_path = (temp_storage_dir / "data").resolve()
        assert manager.base_path == expected_path
        assert (expected_path / "cognition").exists()
    finally:
        del os.environ["DGM_BASE_PATH"]

def test_path_normalization():
    manager = RuntimeStorageManager()
    path = manager.get_path("memory", "../../../etc/passwd")
    assert "etcpasswd" in path.name
    assert "memory" in str(path.parent)

def test_self_healing_isolation(temp_storage_dir):
    os.environ["DGM_STORAGE_PATH"] = str(temp_storage_dir)
    try:
        manager = RuntimeStorageManager()
        filename = "test_corrupt.json"
        manager.save_data("memory", filename, "some data")
        source_path = manager.get_path("memory", filename)
        assert source_path.exists()
        manager.isolate_corrupted("memory", filename)
        assert not source_path.exists()
        corrupted_path = manager.get_path("corrupted", f"memory_{filename}")
        assert corrupted_path.exists()
    finally:
        del os.environ["DGM_STORAGE_PATH"]

def test_read_only_fallback(temp_storage_dir):
    ro_dir = temp_storage_dir / "read_only"
    ro_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(ro_dir, 0o555)
    try:
        manager = RuntimeStorageManager(base_path=str(ro_dir))
        path = manager.get_path("memory", "test.txt")
        assert "/tmp/dgm_fallback" in str(path) or str(ro_dir) in str(path)
    finally:
        os.chmod(ro_dir, 0o777)


def test_storage_manager_frozen_install_migrates_to_per_user_runtime(monkeypatch, tmp_path):
    """A frozen build uses LOCALAPPDATA and copies the old install data without deleting it."""
    monkeypatch.delenv("DGM_STORAGE_PATH", raising=False)
    monkeypatch.delenv("DGM_BASE_PATH", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    executable = tmp_path / "DGM-MAT" / "installed" / "DGM-MAT.exe"
    project_root = executable.parent.parent
    (project_root / ".git").mkdir(parents=True)
    legacy_mission = project_root / "storage" / "runtime" / "missions" / "mission_12345678.json"
    legacy_mission.parent.mkdir(parents=True)
    legacy_mission.write_text('{"mission_id":"mission_12345678"}', encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))

    manager = RuntimeStorageManager()

    expected = tmp_path / "AppData" / "Local" / "DGM-MAT" / "Vault" / "runtime"
    migrated_mission = expected / "missions" / legacy_mission.name
    assert manager.base_path == expected.resolve()
    assert migrated_mission.read_text(encoding="utf-8") == legacy_mission.read_text(encoding="utf-8")
    assert legacy_mission.is_file(), "legacy source must remain untouched"
    assert list((expected / "migration-logs").glob("legacy-runtime-*.json"))


def test_legacy_runtime_conflicts_are_preserved_separately(monkeypatch, tmp_path):
    monkeypatch.delenv("DGM_STORAGE_PATH", raising=False)
    monkeypatch.delenv("DGM_BASE_PATH", raising=False)
    local_data = tmp_path / "AppData" / "Local"
    monkeypatch.setenv("LOCALAPPDATA", str(local_data))
    executable = tmp_path / "DGM-MAT" / "installed" / "DGM-MAT.exe"
    project_root = executable.parent.parent
    (project_root / ".git").mkdir(parents=True)
    legacy_file = project_root / "storage" / "runtime" / "missions" / "mission_conflict.json"
    legacy_file.parent.mkdir(parents=True)
    legacy_file.write_text("legacy checkpoint", encoding="utf-8")
    current_file = local_data / "DGM-MAT" / "Vault" / "runtime" / "missions" / legacy_file.name
    current_file.parent.mkdir(parents=True)
    current_file.write_text("newer checkpoint", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))

    manager = RuntimeStorageManager()

    assert manager.base_path == (local_data / "DGM-MAT" / "Vault" / "runtime").resolve()
    assert current_file.read_text(encoding="utf-8") == "newer checkpoint"
    preserved = list((manager.base_path / "legacy-imports").rglob(legacy_file.name))
    assert len(preserved) == 1
    assert preserved[0].read_text(encoding="utf-8") == "legacy checkpoint"
    assert legacy_file.read_text(encoding="utf-8") == "legacy checkpoint"


def test_runtime_storage_is_nested_under_the_same_vault_override(tmp_path, monkeypatch):
    monkeypatch.delenv("DGM_STORAGE_PATH", raising=False)
    monkeypatch.delenv("DGM_BASE_PATH", raising=False)
    vault_root = tmp_path / "chosen-vault"
    monkeypatch.setenv("DGM_VAULT_PATH", str(vault_root))
    manager = RuntimeStorageManager()
    assert manager.base_path == (vault_root / "runtime").resolve()
