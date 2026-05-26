import subprocess
from pathlib import Path
from typing import Optional
from core.observability.logger import dgm_logger

class WorktreeRuntime:
    def __init__(self, base_path: str = "worktrees"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, branch_name: str) -> Optional[Path]:
        """Creates an isolated git worktree for a branch."""
        target_path = self.base_path / branch_name
        try:
            dgm_logger.info(f"WorktreeRuntime: Creating worktree for {branch_name}")
            subprocess.run(["git", "worktree", "add", str(target_path), branch_name], check=True)
            return target_path
        except Exception as e:
            dgm_logger.error(f"WorktreeRuntime: Failed to create worktree: {e}")
            return None

    def remove_worktree(self, branch_name: str):
        """Cleans up a git worktree."""
        target_path = self.base_path / branch_name
        try:
            dgm_logger.info(f"WorktreeRuntime: Removing worktree for {branch_name}")
            subprocess.run(["git", "worktree", "remove", str(target_path)], check=True)
        except Exception as e:
            dgm_logger.error(f"WorktreeRuntime: Failed to remove worktree: {e}")

    def execute_in_worktree(self, branch_name: str, command: str):
        """Executes a command within an isolated worktree."""
        target_path = self.base_path / branch_name
        if not target_path.exists():
            return None

        try:
            dgm_logger.info(f"WorktreeRuntime: Executing '{command}' in {branch_name}")
            result = subprocess.run(command, shell=True, cwd=target_path, capture_output=True, text=True)
            return result
        except Exception as e:
            dgm_logger.error(f"WorktreeRuntime: Execution failed: {e}")
            return None
