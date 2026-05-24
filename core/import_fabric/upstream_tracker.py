import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class UpstreamTracker:
    """
    Tracks upstream changes for an imported repository.
    """
    def check_for_updates(self, repo_path: Path) -> Dict[str, Any]:
        try:
            subprocess.run(["git", "fetch", "upstream"], cwd=repo_path, check=True, capture_output=True)
            res = subprocess.run(["git", "rev-list", "HEAD..upstream/main", "--count"], cwd=repo_path, capture_output=True, text=True)
            if res.returncode != 0:
                 # Try master if main fails
                 res = subprocess.run(["git", "rev-list", "HEAD..upstream/master", "--count"], cwd=repo_path, capture_output=True, text=True)

            count = int(res.stdout.strip()) if res.returncode == 0 else 0
            return {
                "behind_by": count,
                "needs_update": count > 0
            }
        except Exception:
            return {"behind_by": 0, "needs_update": False, "error": "Could not check upstream"}
