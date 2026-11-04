from pathlib import Path

from core.execution.worktree_manager import WorktreeManager
from core.execution.branch_manager import BranchManager


class ExecutionEngine:
    """Small facade for creating and safely retiring task-specific worktrees."""

    def __init__(
        self,
        *,
        repo_root: str | Path | None = None,
        worktree_base_path: str | Path = ".runtime/worktrees",
    ) -> None:
        self.worktree_mgr = WorktreeManager(
            base_path=worktree_base_path,
            repo_root=repo_root,
        )
        self.branch_mgr = BranchManager()

    def start_execution(self, agent_name: str, task_id: str):
        branch = self.branch_mgr.generate_branch_name(agent_name, task_id)
        path = self.worktree_mgr.create_worktree(branch, task_id)
        return {"path": path, "branch": branch}

    def cleanup_execution(self, task_id: str) -> bool:
        """Remove only a clean task worktree; dirty work remains available for recovery."""
        return self.worktree_mgr.cleanup_worktree(task_id)
