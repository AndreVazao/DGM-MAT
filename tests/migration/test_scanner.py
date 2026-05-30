import pytest
from pathlib import Path
from core.migration.dependency_scanner import DependencyScanner

def test_scan_file(tmp_path):
    base_dir = tmp_path
    core_dir = base_dir / "core"
    core_dir.mkdir()

    file_path = core_dir / "test_mod.py"
    file_path.write_text("import core.api\nfrom shared.models import User")

    scanner = DependencyScanner(str(base_dir))
    item = scanner.scan_file(file_path)

    assert item is not None
    assert item.path == "core/test_mod.py"
    assert "core/api.py" in item.dependencies or "core/api/__init__.py" in item.dependencies
    assert "shared/models.py" in item.dependencies or "shared/models/__init__.py" in item.dependencies

def test_scan_tree(tmp_path):
    base_dir = tmp_path
    (base_dir / "core").mkdir()
    (base_dir / "shared").mkdir()

    (base_dir / "core/a.py").write_text("import shared.b")
    (base_dir / "shared/b.py").write_text("import core.a")

    scanner = DependencyScanner(str(base_dir))
    inventory = scanner.scan_tree()

    assert "core/a.py" in inventory
    assert "shared/b.py" in inventory
    assert inventory["core/a.py"].import_count == 1
    assert inventory["shared/b.py"].import_count == 1
