import json
from pathlib import Path
from typing import List, Dict, Any
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.observability.logger import dgm_logger

class EcosystemValidator:
    REQUIRED_FOLDERS = ["core", "runtime", "config", "docs", "tests", "workflows"]
    REQUIRED_FILES = ["health.json", "ecosystem.json", "README.md", "architecture.md", ".gitignore"]

    def __init__(self, registry: EcosystemRegistry, root_path: Path = Path(".")):
        self.registry = registry
        self.root_path = root_path

    def validate_node(self, node_name: str) -> Dict[str, Any]:
        """Validates a single ecosystem node against the physical structure."""
        node_path = self.root_path / node_name

        # Special case: DGM-MAT-OS might be the root or a subfolder
        if node_name == "DGM-MAT-OS" and not node_path.exists():
             node_path = self.root_path

        results = {
            "node": node_name,
            "exists": node_path.exists(),
            "missing_folders": [],
            "missing_files": [],
            "is_valid": True
        }

        if not node_path.exists():
            results["is_valid"] = False
            return results

        for folder in self.REQUIRED_FOLDERS:
            if not (node_path / folder).is_dir():
                results["missing_folders"].append(folder)
                results["is_valid"] = False

        for file in self.REQUIRED_FILES:
            if not (node_path / file).is_file():
                results["missing_files"].append(file)
                results["is_valid"] = False

        return results

    def validate_all(self) -> List[Dict[str, Any]]:
        """Validates all nodes in the registry."""
        nodes = self.registry.list_nodes()
        reports = []
        for node in nodes:
            report = self.validate_node(node.name)
            reports.append(report)

            if not report["is_valid"]:
                dgm_logger.warning(f"Ecosystem drift detected for {node.name}: {report}")
            else:
                dgm_logger.info(f"Ecosystem node {node.name} is synchronized.")

        return reports

    def get_drift_report(self) -> Dict[str, List[str]]:
        """Returns a summarized drift report."""
        nodes = self.registry.list_nodes()
        drift = {
            "missing_nodes": [],
            "incomplete_nodes": []
        }

        for node in nodes:
            report = self.validate_node(node.name)
            if not report["exists"]:
                drift["missing_nodes"].append(node.name)
            elif not report["is_valid"]:
                drift["incomplete_nodes"].append(node.name)

        return drift

if __name__ == "__main__":
    registry = EcosystemRegistry()
    validator = EcosystemValidator(registry)
    report = validator.get_drift_report()
    print(json.dumps(report, indent=2))
