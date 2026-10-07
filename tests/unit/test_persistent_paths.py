import os
import pytest
from pathlib import Path
from core.storage.storage_manager import RuntimeStorageManager

def test_storage_manager_persistent_path():
    sm = RuntimeStorageManager()
    # The runtime path must be persistent and repository/install configurable,
    # not tied to the historical C:\\DevopGodMode location.
    assert "runtime" in str(sm.base_path).lower()
    assert "devopgodmode" not in str(sm.base_path).lower()

def test_storage_manager_subdirs():
    sm = RuntimeStorageManager()
    assert sm.get_path("missions").name == "missions"
    assert sm.get_path("memory").name == "memory"
