import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.observability.logger import dgm_logger

class CognitiveFilesystem:
    """
    Advanced Workspace Mapping Layer.
    Goes beyond simple file listing to detect stacks, dependencies, and tech debt.
    """
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode"):
        self.workspace_root = Path(workspace_root)
        self.repo_map: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.tech_debt_clusters: List[Dict[str, Any]] = []

    def scan_workspace(self):
        """Perform a deep cognitive scan of the workspace."""
        dgm_logger.info(f"CognitiveFilesystem: Scanning {self.workspace_root}...")
        if not self.workspace_root.exists():
            dgm_logger.warning(f"CognitiveFilesystem: Workspace root {self.workspace_root} does not exist.")
            return

        for repo_path in self.workspace_root.iterdir():
            if repo_path.is_dir() and not repo_path.name.startswith('.'):
                self._analyze_repo(repo_path)

        self._build_dependency_graph()
        dgm_logger.info(f"CognitiveFilesystem: Scan complete. Mapped {len(self.repo_map)} repositories.")

    def _analyze_repo(self, path: Path):
        """Detect stacks, relations and health of a repository."""
        repo_name = path.name
        stats = {
            "name": repo_name,
            "path": str(path),
            "stacks": self._detect_stacks(path),
            "is_active": self._check_activity(path),
            "debt_score": self._estimate_tech_debt(path),
            "dependencies": self._extract_dependencies(path)
        }
        self.repo_map[repo_name] = stats

    def _detect_stacks(self, path: Path) -> List[str]:
        stacks = []
        if (path / "package.json").exists(): stacks.append("nodejs")
        if (path / "requirements.txt").exists() or (path / "setup.py").exists(): stacks.append("python")
        if (path / "go.mod").exists(): stacks.append("go")
        if (path / "Cargo.toml").exists(): stacks.append("rust")
        if (path / "pom.xml").exists(): stacks.append("java")
        if (path / "Dockerfile").exists(): stacks.append("docker")
        return stacks

    def _check_activity(self, path: Path) -> bool:
        # Check if there were any git commits or file changes in the last 30 days
        # Placeholder for real git logic
        return True

    def _estimate_tech_debt(self, path: Path) -> float:
        """Heuristic-based tech debt estimation."""
        debt = 0.0
        # Check for 'TODO' or 'FIXME' counts
        # Check for large files
        # Check for lack of tests directory
        if not (path / "tests").exists() and not (path / "test").exists():
            debt += 0.3
        return min(debt, 1.0)

    def _extract_dependencies(self, path: Path) -> List[str]:
        deps = []
        # Logic to parse package.json or requirements.txt
        return deps

    def _build_dependency_graph(self):
        """Maps relationships between internal repositories."""
        for name, data in self.repo_map.items():
            # Logic to find cross-repo references
            self.dependency_graph[name] = []

    def get_repo_relations(self) -> Dict[str, Any]:
        return {
            "repos": self.repo_map,
            "graph": self.dependency_graph,
            "clusters": self.tech_debt_clusters
        }

# Global instance
cognitive_fs = CognitiveFilesystem()
