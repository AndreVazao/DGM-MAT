import os
import shutil
from pathlib import Path
import pytest
from core.storage.storage_manager import RuntimeStorageManager

@pytest.fixture
def temp_storage_dir(tmp_path):
    storage_dir = tmp_path / "dgm_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir

def test_storage_manager_default_path():
    """Default path is repository/install relative, not the historical machine path."""
    manager = RuntimeStorageManager()
    assert "devopgodmode" not in str(manager.base_path).lower()
    assert "storage" in manager.base_path.parts and "runtime" in manager.base_path.parts

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
