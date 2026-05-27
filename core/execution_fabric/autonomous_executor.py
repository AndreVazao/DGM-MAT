from core.observability.logger import dgm_logger
from core.execution_fabric.worktree_runtime import WorktreeRuntime
from core.execution_fabric.execution_supervisor import ExecutionSupervisor
from core.execution_fabric.safe_patch_engine import SafePatchEngine
from core.execution.approval_manager import approval_manager, ApprovalStatus

class AutonomousExecutor:
    """
    Main engine for executing autonomous development tasks.
    Enforces the approval flow for mission tasks.
    """
    def __init__(self):
        self.runtime = WorktreeRuntime()
        self.supervisor = ExecutionSupervisor()
        self.patch_engine = SafePatchEngine()

    def execute_task(self, task: dict):
        task_id = task.get('id', 'unknown')
        dgm_logger.info(f"AutonomousExecutor: Starting task {task_id}")

        if not self.supervisor.validate_plan(task):
            dgm_logger.error("Execution rejected by supervisor")
            return False

        try:
            # Create sandbox
            worktree_path = self.runtime.create_sandbox(task_id)

            # Execute implementation logic (simulated)
            dgm_logger.info(f"Executing in {worktree_path}")

            # Generate patch
            patch = self.patch_engine.generate_patch(worktree_path)

            # Assess risk
            risk_info = self.patch_engine.assess_risk(patch)

            # Check if this task already has a pending approval
            approval_required = task.get("approval_required", False) or risk_info["level"] in ["HIGH", "CRITICAL"]

            # Validate patch via supervisor
            if self.supervisor.authorize_commit(patch, task_id, approval_required):
                self.patch_engine.apply_patch(patch)
                dgm_logger.info("Task executed and patch applied successfully")
                return True
            else:
                if approval_required:
                    dgm_logger.warning(f"Task {task_id} is AWAITING APPROVAL.")
                    # Update approval entry with risk info
                    if task_id in approval_manager.approvals:
                        approval_manager.approvals[task_id].update({
                            "risk_score": risk_info["score"],
                            "impact": risk_info["level"]
                        })
                return False

        except Exception as e:
            dgm_logger.error(f"Execution failed: {e}")
            return False
        finally:
            self.runtime.cleanup_sandbox(task_id)

        return False
