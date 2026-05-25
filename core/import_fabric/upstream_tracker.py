import subprocess  # nosec
from pathlib import Path
from typing import Dict, Any, Optional
from core.execution.git_utils import run_git_command

class UpstreamTracker:
    def check_updates(self, repo_path: Path) -> Dict[str, Any]:
        """Checks for new commits in upstream."""
        try:
            run_git_command(["fetch", "upstream"], cwd=repo_path)
            res = run_git_command(["rev-list", "HEAD..upstream/main", "--count"], cwd=repo_path)
            if res.returncode != 0:
                 # Try master if main fails
                 res = run_git_command(["rev-list", "HEAD..upstream/master", "--count"], cwd=repo_path)

            count = int(res.stdout.strip()) if res and res.returncode == 0 else 0
            return {
                "behind": count,
                "status": "outdated" if count > 0 else "up-to-date"
            }
        except Exception:
            return {"behind": 0, "status": "unknown"}
