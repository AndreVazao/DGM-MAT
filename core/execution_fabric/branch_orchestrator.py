from core.observability.logger import dgm_logger
import subprocess  # nosec

class BranchOrchestrator:
    """
    Manages branches for complex multi-step development cycles.
    """
    def create_feature_branch(self, task_id: str):
        branch_name = f"feat-{task_id}"
        dgm_logger.info(f"BranchOrchestrator: Creating branch {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)  # nosec

    def merge_to_main(self, branch_name: str):
        dgm_logger.info(f"BranchOrchestrator: Merging {branch_name} to main")
        # Safety checks before merge
        pass
