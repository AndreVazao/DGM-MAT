import subprocess  # nosec
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from core.observability.logger import dgm_logger
from core.execution.git_utils import run_git_command, ensure_branch

class RepoCloner:
    """
    Clones external repositories into isolated branches and generates metadata.
    """
    def __init__(self, base_path: Path = Path("labs/external")):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def clone(self, repo_url: str, name: Optional[str] = None) -> Optional[Path]:
        if not name:
            name = repo_url.split("/")[-1].replace(".git", "")

        target_path = self.base_path / name

        if target_path.exists():
            dgm_logger.info(f"Repo {name} already exists at {target_path}. Updating...")
            # For now, just return existing path, real update logic can be added
            return target_path

        dgm_logger.info(f"Cloning {repo_url} into {target_path}...")
        try:
            run_git_command(["clone", "--depth", "1", repo_url, str(target_path)])

            # Create isolated branch
            ensure_branch(f"external/import/{name}", cwd=target_path)

            # Generate dgm-meta.json
            meta = {
                "name": name,
                "source": repo_url,
                "import_date": datetime.now().isoformat(),
                "status": "cloned",
                "branch": f"external/import/{name}"
            }
            with open(target_path / "dgm-meta.json", "w") as f:
                json.dump(meta, f, indent=2)

            return target_path
        except Exception as e:
            dgm_logger.error(f"Failed to clone {repo_url}: {e}")
            return None
