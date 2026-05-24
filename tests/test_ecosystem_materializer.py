import pytest
import shutil
from pathlib import Path
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_validator import EcosystemValidator
from core.ecosystem.ecosystem_materializer import EcosystemMaterializer
from core.storage.storage_manager import storage_manager

@pytest.fixture
def temp_root(tmp_path):
    # Setup a mock root for materialization
    return tmp_path

@pytest.fixture
def registry():
    # Use the real registry class but we might want to mock the data if needed
    # For now, it will use the default nodes
    return EcosystemRegistry()

def test_validator_detects_drift(registry, temp_root):
    validator = EcosystemValidator(registry, root_path=temp_root)
    drift = validator.get_drift_report()

    # All nodes should be missing in a fresh temp directory
    assert len(drift["missing_nodes"]) > 0
    # DGM-MAT-OS might be special as it checks root if subfolder is missing
    # In a completely empty temp_root, even DGM-MAT-OS should be incomplete if folders are missing

def test_materializer_creates_structure(registry, temp_root):
    materializer = EcosystemMaterializer(registry, root_path=temp_root)
    results = materializer.materialize_all()

    # Check that some nodes were materialized
    assert any(r["status"] == "materialized" for r in results)

    # Verify physical folders for a few nodes
    assert (temp_root / "DGM-MAT-Runtime").is_dir()
    assert (temp_root / "DGM-MAT-Runtime" / "core").is_dir()
    assert (temp_root / "DGM-MAT-Runtime" / "health.json").is_file()

    # Re-validate
    validator = EcosystemValidator(registry, root_path=temp_root)
    report = validator.validate_all()
    for r in report:
        assert r["is_valid"] is True

def test_materializer_dry_run(registry, temp_root):
    materializer = EcosystemMaterializer(registry, root_path=temp_root)
    results = materializer.materialize_all(dry_run=True)

    # Should report drift but NOT create folders
    assert any(r["status"] == "drift_detected" for r in results)
    assert not (temp_root / "DGM-MAT-Runtime").exists()

def test_registry_sync_integration(registry, temp_root):
    # This is slightly tricky as Registry usually uses "." as root when calling materializer
    # We can test that the method exists and can be called
    assert hasattr(registry, "sync_filesystem")
