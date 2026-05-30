import os
import shutil
import json
import pytest
from pathlib import Path
from core.autonomous_dev.repository_extractor import RepositoryExtractor

@pytest.fixture
def temp_workspace(tmp_path):
    # Create a mock workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create some mock modules
    (workspace / "core" / "runtime").mkdir(parents=True)
    with open(workspace / "core" / "runtime" / "engine.py", "w") as f:
        f.write("import core.runtime_state.store\nimport os\n")

    (workspace / "core" / "runtime_state").mkdir(parents=True)
    with open(workspace / "core" / "runtime_state" / "store.py", "w") as f:
        f.write("class Store: pass\n")

    (workspace / "core" / "other").mkdir(parents=True)
    with open(workspace / "core" / "other" / "utils.py", "w") as f:
        f.write("def helper(): pass\n")

    # Mock import from 'other' which should be detected as broken for 'runtime' component
    with open(workspace / "core" / "runtime" / "broken.py", "w") as f:
        f.write("import core.other.utils\n")

    # Create manifest
    manifest_path = workspace / "config" / "extraction_manifest.json"
    manifest_path.parent.mkdir()
    manifest_data = {
        "runtime": [
            "core/runtime",
            "core/runtime_state"
        ]
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)

    return workspace, manifest_path

def test_extraction_copies_files(temp_workspace):
    workspace, manifest_path = temp_workspace
    extractor = RepositoryExtractor(str(manifest_path), base_dir=str(workspace))

    # Target directory for extraction
    dest_dir = workspace.parent / "DGM-MAT-Runtime"

    success = extractor.extract("runtime")
    assert success is True

    # Verify files exist in destination
    assert (dest_dir / "core" / "runtime" / "engine.py").exists()
    assert (dest_dir / "core" / "runtime_state" / "store.py").exists()
    # Ensure 'other' was NOT copied
    assert not (dest_dir / "core" / "other").exists()

def test_dry_run_no_copy(temp_workspace):
    workspace, manifest_path = temp_workspace
    extractor = RepositoryExtractor(str(manifest_path), base_dir=str(workspace))

    dest_dir = workspace.parent / "DGM-MAT-Runtime"

    success = extractor.extract("runtime", dry_run=True)
    assert success is True
    assert not dest_dir.exists()

def test_detect_broken_imports(temp_workspace):
    workspace, manifest_path = temp_workspace
    extractor = RepositoryExtractor(str(manifest_path), base_dir=str(workspace))

    extractor.extract("runtime")

    broken_imports_path = workspace / "reports" / "extraction" / "broken_imports.json"
    assert broken_imports_path.exists()

    with open(broken_imports_path, "r") as f:
        broken = json.load(f)

    # 'broken.py' should have a broken import to 'core.other.utils'
    # because 'core/other' is not in the manifest for 'runtime'
    assert any("core/runtime/broken.py" in key for key in broken.keys())
    assert any("core.other.utils" in str(val) for val in broken.values())
