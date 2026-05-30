import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from .migration_manifest import (
    ModuleInventory,
    ModuleInventoryItem,
    MigrationPlan,
    MigrationPlanItem,
    DuplicateReport,
    OrphanReport
)
from .dependency_scanner import DependencyScanner
from .module_classifier import ModuleClassifier
from .module_exporter import ModuleExporter

class MigrationEngine:
    def __init__(self, base_dir: str = ".", output_dir: str = ".runtime/migration"):
        self.base_dir = Path(base_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scanner = DependencyScanner(str(self.base_dir))
        self.classifier = ModuleClassifier()
        self.exporter = ModuleExporter(base_dir=str(self.base_dir))

        self.inventory: Optional[ModuleInventory] = None

    def full_scan(self) -> ModuleInventory:
        raw_inventory = self.scanner.scan_tree()
        classified_inventory = self.classifier.classify(raw_inventory)
        self.inventory = ModuleInventory(modules=classified_inventory)

        self._save_json("module_inventory.json", self.inventory.model_dump())

        duplicates = self.classifier.generate_duplicate_report(classified_inventory)
        self._save_json("duplicates.json", duplicates.model_dump())

        orphans = self.classifier.generate_orphan_report(classified_inventory)
        self._save_json("orphans.json", orphans.model_dump())

        return self.inventory

    def create_migration_plan(self, approved_categories: List[str] = ["CORE", "OPTIONAL"]) -> MigrationPlan:
        if not self.inventory:
            self.full_scan()

        items = []
        for path, item in self.inventory.modules.items():
            if item.category in approved_categories:
                items.append(MigrationPlanItem(
                    source_path=path,
                    target_path=path # Preserving structure in the new core
                ))

        plan = MigrationPlan(items=items)
        self._save_json("migration_plan.json", plan.model_dump())
        return plan

    def execute_migration(self, plan: Optional[MigrationPlan] = None) -> bool:
        if not plan:
            plan = self.create_migration_plan()

        return self.exporter.export_plan(plan)

    def _save_json(self, filename: str, data: Dict):
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    engine = MigrationEngine()
    print("Starting full repository scan...")
    inventory = engine.full_scan()
    print(f"Scan complete. Found {len(inventory.modules)} modules.")
    print(f"Reports generated in .runtime/migration/")
