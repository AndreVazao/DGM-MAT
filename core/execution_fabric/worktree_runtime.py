import subprocess  # nosec
import os
from pathlib import Path
from core.observability.logger import dgm_logger

class WorktreeRuntime:
    """
    Manages isolated git worktrees for autonomous execution.
    """
    def __init__(self, base_path: str = ".runtime/worktrees"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_sandbox(self, task_id: str) -> Path:
        branch_name = f"exec-{task_id}"
        worktree_path = self.base_path / task_id

        dgm_logger.info(f"WorktreeRuntime: Creating sandbox for {task_id} at {worktree_path}")

        try:
            # git worktree add -b <branch> <path>
            subprocess.run(  # nosec
                ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
                check=True,
                capture_output=True
            )
            return worktree_path
        except subprocess.CalledProcessError as e:
            dgm_logger.error(f"Failed to create worktree: {e.stderr.decode()}")
            raise

    def cleanup_sandbox(self, task_id: str):
        worktree_path = self.base_path / task_id
        dgm_logger.info(f"WorktreeRuntime: Cleaning up sandbox for {task_id}")

        if worktree_path.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], check=True)  # nosec
            # Delete branch
            subprocess.run(["git", "branch", "-D", f"exec-{task_id}"], check=False)  # nosec
