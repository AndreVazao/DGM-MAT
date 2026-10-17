from core.observability.logger import dgm_logger

class BranchExecutionManager:
    FORBIDDEN_BRANCHES = {"main", "master", "prod", "production"}

    def create_isolated_branch(self, branch_name: str):
        if branch_name in self.FORBIDDEN_BRANCHES:
            dgm_logger.error(f"BranchExecution: Cannot create/write directly to protected branch: {branch_name}")
            return False

        dgm_logger.info(f"Branch Execution: Creating branch {branch_name}...")
        # git branch {branch_name}
        return True

    def push_changes(self, branch_name: str, force: bool = False):
        if force:
            dgm_logger.error(f"BranchExecution: Force push is strictly FORBIDDEN.")
            return False
        dgm_logger.info(f"Branch Execution: Pushing {branch_name} to remote...")
        return True

    def delete_branch(self, branch_name: str):
        # Autonomous deletion is restricted
        dgm_logger.warning(f"BranchExecution: Automatic branch deletion requested for {branch_name}. Blocked for safety.")
        return False
