from core.observability.logger import dgm_logger
from pathlib import Path
import subprocess

class SafePatchEngine:
    """
    Generates and applies reversible patches for repository modification.
    """
    def generate_patch(self, worktree_path: Path) -> str:
        dgm_logger.info(f"SafePatchEngine: Generating patch from {worktree_path}")
        try:
            result = subprocess.run(
                ["git", "-C", str(worktree_path), "diff"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def apply_patch(self, patch: str):
        dgm_logger.info("SafePatchEngine: Applying patch to main repository")
        if not patch:
            return

        try:
            subprocess.run(
                ["git", "apply"],
                input=patch,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            dgm_logger.error(f"Failed to apply patch: {e}")
            raise
