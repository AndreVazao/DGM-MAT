import os
import pytest
from pathlib import Path
from core.storage.storage_manager import RuntimeStorageManager

def test_storage_manager_persistent_path():
    sm = RuntimeStorageManager()
    if os.name == 'nt':
        assert "DevopGodMode" in str(sm.base_path)
    else:
        assert "runtime" in str(sm.base_path)

def test_storage_manager_subdirs():
    sm = RuntimeStorageManager()
    assert sm.get_path("missions").name == "missions"
    assert sm.get_path("memory").name == "memory"
