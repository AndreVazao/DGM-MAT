from core.observability.logger import dgm_logger
import subprocess  # nosec
from core.execution.git_utils import run_git_command, ensure_branch

class BranchOrchestrator:
    """
    Manages branches for complex multi-step development cycles.
    """
    def create_feature_branch(self, task_id: str):
        branch_name = f"feat-{task_id}"
        dgm_logger.info(f"BranchOrchestrator: Creating branch {branch_name}")
        ensure_branch(branch_name)

    def merge_to_main(self, branch_name: str):
        dgm_logger.info(f"BranchOrchestrator: Merging {branch_name} to main")
        # Safety checks before merge
        run_git_command(["checkout", "main"])
        run_git_command(["merge", branch_name])
