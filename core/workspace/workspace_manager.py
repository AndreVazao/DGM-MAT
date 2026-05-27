import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class WorkspaceManager:
    """
    Requirement 4 & 5: Repository Workspace & Persistent Evolution Memory.
    Treats C:\\ProgramasGodMode as the canonical multi-repository workspace.
    """
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode"):
        self.root = Path(workspace_root)
        if os.name == 'nt' and not self.root.exists():
            try:
                self.root.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                dgm_logger.warning(f"WorkspaceManager: Could not create root {workspace_root}: {e}")

        self.memory_repo = self.root / "andreos-memory"
        self._ensure_memory_repo()

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
            for item in self.root.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    repos.append(item)
        except (PermissionError, OSError):
            dgm_logger.error(f"WorkspaceManager: Permission denied scanning {self.root}")
        return repos

    def get_repo_health(self, repo_path: Path) -> Dict[str, Any]:
        health = {
            "name": repo_path.name,
            "path": str(repo_path),
            "is_git": (repo_path / ".git").exists(),
            "status": "unknown",
            "branch": "unknown",
            "uncommitted_changes": False
        }
        if health["is_git"]:
            try:
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=str(repo_path), stderr=subprocess.DEVNULL
                ).decode().strip()
                health["branch"] = branch
                status_out = subprocess.check_output(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo_path), stderr=subprocess.DEVNULL
                ).decode().strip()
                health["uncommitted_changes"] = len(status_out) > 0
                health["status"] = "dirty" if health["uncommitted_changes"] else "clean"
            except Exception:
                health["status"] = "git_error"
        return health

    def scan_workspace(self) -> List[Dict[str, Any]]:
        repos = self.discover_repositories()
        return [self.get_repo_health(repo) for repo in repos]

    def sync_memory_repo(self):
        """Requirement 5: Automatic sync support for evolution memory."""
        if not self.memory_repo.exists():
            return {"status": "error", "message": "Memory repository missing"}
        try:
            # Stage everything
            subprocess.run(["git", "add", "."], cwd=str(self.memory_repo), capture_output=True)
            # Commit if changes
            subprocess.run(["git", "commit", "-m", "Auto-sync evolution memory"], cwd=str(self.memory_repo), capture_output=True)
            # Placeholder for git push/pull logic
            dgm_logger.info(f"WorkspaceManager: Sync complete for {self.memory_repo}")
            return {"status": "success", "repo": str(self.memory_repo)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

workspace_manager = WorkspaceManager()
