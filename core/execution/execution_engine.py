from core.execution.worktree_manager import WorktreeManager
from core.execution.branch_manager import BranchManager

class ExecutionEngine:
    def __init__(self):
        self.worktree_mgr = WorktreeManager()
        self.branch_mgr = BranchManager()

    def start_execution(self, agent_name: str, task_id: str):
        branch = self.branch_mgr.generate_branch_name(agent_name, task_id)
        path = self.worktree_mgr.create_worktree(agent_name, task_id, branch)
        return {"path": path, "branch": branch}
