import json
import os
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemStatus
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class RealitySyncEngine:
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode"):
        self.registry = EcosystemRegistry()
        self.workspace_root = Path(workspace_root)
        self.manual_clones_root = self.workspace_root / "manual_clones"
        self.report_path = storage_manager.get_path("federation", "ecosystem_status.json")

    def run_sync(self) -> Dict[str, Any]:
        """
        Compares registered repos vs real repos and detects anomalies.
        """
        dgm_logger.info("RealitySyncEngine: Starting ecosystem reality sync...")

        registered_nodes = self.registry.list_nodes()
        registered_names = {node.name for node in registered_nodes}

        real_repos = self._scan_real_repos()
        real_repo_names = {path.name for path in real_repos}

        missing_repos = registered_names - real_repo_names
        orphan_repos = real_repo_names - registered_names

        # Detect broken paths (registered but directory missing or empty)
        broken_paths = []
        for node in registered_nodes:
            node_path = self.workspace_root / node.name
            if not node_path.exists() and node.status not in [EcosystemStatus.PLANNED, EcosystemStatus.RESERVED]:
                 broken_paths.append(node.name)

        # Detect duplicated registrations (names that map to the same physical path - less likely with this design but good to check)
        # For now, we focus on the name-to-path mapping

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_registered": len(registered_names),
                "total_physical": len(real_repo_names),
                "missing": len(missing_repos),
                "orphans": len(orphan_repos),
                "broken": len(broken_paths)
            },
            "details": {
                "missing": list(missing_repos),
                "orphans": list(orphan_repos),
                "broken": broken_paths
            }
        }

        self._save_report(report)
        dgm_logger.info(f"RealitySyncEngine: Sync complete. Status saved to {self.report_path}")
        return report

    def _scan_real_repos(self) -> List[Path]:
        repos = []
        # Scan root
        if self.workspace_root.exists():
            for item in self.workspace_root.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    repos.append(item)

        # Scan manual_clones
        if self.manual_clones_root.exists():
            for item in self.manual_clones_root.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    repos.append(item)

        return repos

    def _save_report(self, report: Dict[str, Any]):
        try:
            self.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        except Exception as e:
            dgm_logger.error(f"RealitySyncEngine: Failed to save report: {e}")

if __name__ == "__main__":
    # For testing in non-Windows environments, override root if needed
    workspace = os.getenv("DGM_WORKSPACE", "C:/ProgramasGodMode")
    engine = RealitySyncEngine(workspace_root=workspace)
    print(json.dumps(engine.run_sync(), indent=2))
