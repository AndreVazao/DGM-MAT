from typing import Dict, List
from .migration_manifest import ModuleInventoryItem, ModuleCategory, DuplicateReport, OrphanReport

class ModuleClassifier:
    def __init__(self):
        self.core_patterns = ["core/api", "core/runtime", "core/api/runtime_api.py", "core/runtime/runtime_state_store.py"]
        self.legacy_patterns = ["legacy/", "old_", "_v1"]
        self.experimental_patterns = ["experimental/", "lab/", "research/"]

    def classify(self, inventory: Dict[str, ModuleInventoryItem]) -> Dict[str, ModuleInventoryItem]:
        # Step 1: Detect Duplicates
        hash_map: Dict[str, List[str]] = {}
        for path, item in inventory.items():
            if item.hash not in hash_map:
                hash_map[item.hash] = []
            hash_map[item.hash].append(path)

        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

        # Step 2: Apply categories
        for path, item in inventory.items():
            # Check for orphans
            if item.import_count == 0 and not self._is_entrypoint(path):
                item.category = ModuleCategory.ORPHAN

            # Check for duplicates
            elif any(path in paths for paths in duplicates.values()):
                # Keep the first one as CORE/OPTIONAL, others as DUPLICATE
                for h, paths in duplicates.items():
                    if path in paths and path != paths[0]:
                        item.category = ModuleCategory.DUPLICATE
                        break

            # Check for CORE
            elif any(p in path for p in self.core_patterns):
                item.category = ModuleCategory.CORE

            # Check for LEGACY
            elif any(p in path for p in self.legacy_patterns):
                item.category = ModuleCategory.LEGACY

            # Check for EXPERIMENTAL
            elif any(p in path for p in self.experimental_patterns):
                item.category = ModuleCategory.EXPERIMENTAL

            else:
                item.category = ModuleCategory.OPTIONAL

            # Risk Score calculation
            item.risk_score = self._calculate_risk(item)

        return inventory

    def _is_entrypoint(self, path: str) -> bool:
        entrypoints = ["main.py", "run.py", "app.py", "scripts/"]
        return any(path.startswith(e) or path.endswith(e) for e in entrypoints)

    def _calculate_risk(self, item: ModuleInventoryItem) -> float:
        score = 0.0
        # High dependency count increases risk
        score += min(item.dependency_count * 0.1, 0.5)
        # Being a CORE module increases risk
        if item.category == ModuleCategory.CORE:
            score += 0.3
        # LARGE files have more risk
        if item.file_size > 50000: # 50kb
            score += 0.2
        return min(score, 1.0)

    def generate_duplicate_report(self, inventory: Dict[str, ModuleInventoryItem]) -> DuplicateReport:
        hash_map: Dict[str, List[str]] = {}
        for path, item in inventory.items():
            if item.hash not in hash_map:
                hash_map[item.hash] = []
            hash_map[item.hash].append(path)
        return DuplicateReport(duplicates={h: paths for h, paths in hash_map.items() if len(paths) > 1})

    def generate_orphan_report(self, inventory: Dict[str, ModuleInventoryItem]) -> OrphanReport:
        orphans = [path for path, item in inventory.items() if item.category == ModuleCategory.ORPHAN]
        return OrphanReport(orphans=orphans)
