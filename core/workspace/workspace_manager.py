import os
import subprocess
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.observability.logger import dgm_logger

class WorkspaceManager:
    """
    Requirement 4 & 5: Repository Workspace & Persistent Evolution Memory.
    Treats C:/ProgramasGodMode as the canonical multi-repository workspace.
    """
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode"):
        self.root = Path(workspace_root)
        self.manual_clones_root = self.root / "manual_clones"
        self.protected_config_path = Path("config/protected_assets.yaml")
        self.protected_assets = self._load_protected_assets()

        if os.name == 'nt' and not self.root.exists():
            try:
                self.root.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                dgm_logger.warning(f"WorkspaceManager: Could not create root {workspace_root}: {e}")

        if os.name == 'nt' and not self.manual_clones_root.exists():
            try:
                self.manual_clones_root.mkdir(parents=True, exist_ok=True)
                dgm_logger.info(f"WorkspaceManager: Created manual clones directory at {self.manual_clones_root}")
            except Exception as e:
                dgm_logger.warning(f"WorkspaceManager: Could not create manual clones directory: {e}")

        self.memory_repo = self.root / "andreos-memory"
        self._ensure_memory_repo()

    def _load_protected_assets(self) -> Dict[str, Any]:
        if self.protected_config_path.exists():
            try:
                with open(self.protected_config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                dgm_logger.error(f"WorkspaceManager: Failed to load protected assets: {e}")
        return {}

    def is_protected(self, path: str) -> bool:
        """
        Checks if a given path (relative or absolute) is protected.
        """
        path_obj = Path(path)

        # Check protected workflows
        protected_workflows = self.protected_assets.get("protected_workflows", [])
        for workflow in protected_workflows:
            if str(path_obj).endswith(workflow):
                return True

        # Check protected paths
        protected_paths = self.protected_assets.get("protected_paths", [])
        for p in protected_paths:
            # Check if path is inside a protected root (like manual_clones)
            if p in str(path_obj.absolute()) or p in str(path_obj):
                return True

        # Hardcoded rule for manual_clones directory
        if "manual_clones" in str(path_obj.absolute()):
            return True

        return False

    def _ensure_memory_repo(self):
        """Requirement 5: Persistent Evolution Memory repo setup."""
        if os.name == 'nt' and not self.memory_repo.exists():
             try:
                self.memory_repo.mkdir(parents=True, exist_ok=True)
                # Initialize git if not already
                if not (self.memory_repo / ".git").exists():
                    subprocess.run(["git", "init"], cwd=str(self.memory_repo), capture_output=True)
                    dgm_logger.info(f"WorkspaceManager: Initialized memory repo at {self.memory_repo}")
             except Exception as e:
                dgm_logger.warning(f"WorkspaceManager: Could not setup memory repo: {e}")

    def discover_repositories(self) -> List[Path]:
        repos = []
        if not self.root.exists():
            return repos
        try:
            # Discover in root
            for item in self.root.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    repos.append(item)

            # Discover in manual_clones
            if self.manual_clones_root.exists():
                for item in self.manual_clones_root.iterdir():
                    if item.is_dir() and (item / ".git").exists():
                        repos.append(item)

        except (PermissionError, OSError):
            dgm_logger.error(f"WorkspaceManager: Permission denied scanning {self.root}")
        return repos

    def get_repo_health(self, repo_path: Path) -> Dict[str, Any]:
        health = {
            "name": repo_path.name,
            "path": str(repo_path),
            "is_protected": self.is_protected(str(repo_path)),
            "is_manual": "manual_clones" in str(repo_path.absolute())
        }
        return health
