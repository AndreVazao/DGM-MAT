import subprocess  # nosec
from pathlib import Path
from typing import Dict, Any, Optional

class UpstreamTracker:
    def check_updates(self, repo_path: Path) -> Dict[str, Any]:
        """Checks for new commits in upstream."""
        try:
            subprocess.run(["git", "fetch", "upstream"], cwd=repo_path, check=True, capture_output=True)  # nosec
            res = subprocess.run(["git", "rev-list", "HEAD..upstream/main", "--count"], cwd=repo_path, capture_output=True, text=True)  # nosec
            if res.returncode != 0:
                 # Try master if main fails
                 res = subprocess.run(["git", "rev-list", "HEAD..upstream/master", "--count"], cwd=repo_path, capture_output=True, text=True)  # nosec

            count = int(res.stdout.strip()) if res and res.returncode == 0 else 0
            return {
                "behind": count,
                "status": "outdated" if count > 0 else "up-to-date"
            }
        except Exception:
            return {"behind": 0, "status": "unknown"}
