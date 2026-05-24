import json
import os
from pathlib import Path
from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class EcosystemMaterializer:
    def __init__(self, registry: Any, root_path: Path = Path(".")):
        from core.ecosystem.ecosystem_validator import EcosystemValidator
        self.registry = registry
        self.root_path = root_path
        self.validator = EcosystemValidator(registry, root_path)

    def materialize_node(self, node_name: str, dry_run: bool = False) -> Dict[str, Any]:
        """Materializes the physical structure for a single ecosystem node."""
        report = self.validator.validate_node(node_name)
        node = self.registry.get_node(node_name)

        if not node:
            return {"status": "error", "message": f"Node {node_name} not found in registry"}

        node_path = self.root_path / node_name
        if node_name == "DGM-MAT-OS" and not node_path.exists():
            node_path = self.root_path

        actions = []

        if not node_path.exists():
            if not dry_run:
                node_path.mkdir(parents=True, exist_ok=True)
            actions.append(f"Created node directory: {node_path}")

        for folder in self.validator.REQUIRED_FOLDERS:
            target_folder = node_path / folder
            if not target_folder.is_dir():
                if not dry_run:
                    target_folder.mkdir(parents=True, exist_ok=True)
                actions.append(f"Created folder: {target_folder}")

        for file in self.validator.REQUIRED_FILES:
            target_file = node_path / file
            if not target_file.is_file():
                content = self._get_default_content(file, node)
                if not dry_run:
                    target_file.write_text(json.dumps(content, indent=2), encoding="utf-8")
                actions.append(f"Created file: {target_file}")

        if not dry_run and actions:
            dgm_logger.info(f"Materialized {node_name}: {len(actions)} actions performed.")

        return {
            "node": node_name,
            "actions": actions,
            "status": "synchronized" if not actions else ("materialized" if not dry_run else "drift_detected")
        }

    def _get_default_content(self, filename: str, node: Any) -> Dict[str, Any]:
        if filename == "health.json":
            return {
                "node": node.name,
                "status": "healthy",
                "last_check": node.last_sync.isoformat(),
                "score": node.health_score,
                "components": {}
            }
        elif filename == "ecosystem.json":
            return {
                "name": node.name,
                "role": node.role,
                "version": "0.1.0",
                "dependencies": node.dependencies,
                "metadata": node.metadata
            }
        return {}

    def materialize_all(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Materializes all nodes in the registry."""
        nodes = self.registry.list_nodes()
        results = []
        for node in nodes:
            result = self.materialize_node(node.name, dry_run=dry_run)
            results.append(result)
        return results

if __name__ == "__main__":
    import sys
    from core.ecosystem.ecosystem_registry import EcosystemRegistry
    registry = EcosystemRegistry()
    materializer = EcosystemMaterializer(registry)
    dry_run = "--fix" not in sys.argv
    results = materializer.materialize_all(dry_run=dry_run)
    print(json.dumps(results, indent=2))
