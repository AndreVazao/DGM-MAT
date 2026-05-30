import pytest
import json
from pathlib import Path
from core.migration.migration_engine import MigrationEngine

def test_engine_full_scan(tmp_path):
    base_dir = tmp_path
    output_dir = base_dir / ".runtime/migration"

    # Create dummy structure
    (base_dir / "core").mkdir()
    (base_dir / "core/api.py").write_text("class API: pass")

    engine = MigrationEngine(base_dir=str(base_dir), output_dir=str(output_dir))
    inventory = engine.full_scan()

    assert "core/api.py" in inventory.modules
    assert (output_dir / "module_inventory.json").exists()
    assert (output_dir / "duplicates.json").exists()
    assert (output_dir / "orphans.json").exists()

def test_engine_migration_plan(tmp_path):
    base_dir = tmp_path
    output_dir = base_dir / ".runtime/migration"

    (base_dir / "core").mkdir()
    (base_dir / "core/api.py").write_text("class API: pass")

    engine = MigrationEngine(base_dir=str(base_dir), output_dir=str(output_dir))
    # We need to manually set categories or fix classifier to match core/api.py
    inventory = engine.full_scan()

    plan = engine.create_migration_plan(approved_categories=["CORE", "OPTIONAL", "ORPHAN"])

    assert len(plan.items) > 0
    assert (output_dir / "migration_plan.json").exists()
