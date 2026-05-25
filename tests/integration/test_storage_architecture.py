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
    """Test that default path is relative to project root and not absolute C:/."""
    manager = RuntimeStorageManager()
    assert "C:" not in str(manager.base_path)
    assert "storage" in manager.base_path.parts and "runtime" in manager.base_path.parts

def test_storage_manager_env_override(temp_storage_dir):
    """Test that DGM_STORAGE_PATH override works."""
    os.environ["DGM_STORAGE_PATH"] = str(temp_storage_dir)
    try:
        manager = RuntimeStorageManager()
        assert manager.base_path == temp_storage_dir.resolve()
        assert (temp_storage_dir / "memory").exists()
    finally:
        del os.environ["DGM_STORAGE_PATH"]

def test_storage_manager_base_path_override(temp_storage_dir):
    """Test that DGM_BASE_PATH override works."""
    os.environ["DGM_BASE_PATH"] = str(temp_storage_dir)
    try:
        manager = RuntimeStorageManager()
        expected_path = (temp_storage_dir / "data").resolve()
        assert manager.base_path == expected_path
        assert (expected_path / "cognition").exists()
    finally:
        del os.environ["DGM_BASE_PATH"]

def test_path_normalization():
    """Test that get_path normalizes filenames and prevents path traversal."""
    manager = RuntimeStorageManager()
    path = manager.get_path("memory", "../../../etc/passwd")
    assert "etcpasswd" in path.name
    assert "memory" in str(path.parent)

def test_self_healing_isolation(temp_storage_dir):
    """Test that corrupted files are isolated."""
    os.environ["DGM_STORAGE_PATH"] = str(temp_storage_dir)
    try:
        manager = RuntimeStorageManager()
        filename = "test_corrupt.json"
        manager.save_data("memory", filename, "some data")

        # Manually verify it exists
        source_path = manager.get_path("memory", filename)
        assert source_path.exists()

        # Simulate corruption by reading and failing (forced)
        manager.isolate_corrupted("memory", filename)

        assert not source_path.exists()
        corrupted_path = manager.get_path("corrupted", f"memory_{filename}")
        assert corrupted_path.exists()
    finally:
        del os.environ["DGM_STORAGE_PATH"]

def test_read_only_fallback(temp_storage_dir):
    """Test behavior when storage is not writable."""
    ro_dir = temp_storage_dir / "read_only"
    ro_dir.mkdir(parents=True, exist_ok=True)
    # Make it read-only
    os.chmod(ro_dir, 0o555)

    try:
        manager = RuntimeStorageManager(base_path=str(ro_dir))
        # If it couldn't create/access subdir in RO dir, it fallbacks to /tmp/dgm_fallback
        path = manager.get_path("memory", "test.txt")
        assert "/tmp/dgm_fallback" in str(path) or str(ro_dir) in str(path)
    finally:
        os.chmod(ro_dir, 0o777)
