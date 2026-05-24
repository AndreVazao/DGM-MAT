from core.observability.logger import dgm_logger
from core.execution_fabric.worktree_runtime import WorktreeRuntime
from core.execution_fabric.execution_supervisor import ExecutionSupervisor
from core.execution_fabric.safe_patch_engine import SafePatchEngine

class AutonomousExecutor:
    """
    Main engine for executing autonomous development tasks.
    """
    def __init__(self):
        self.runtime = WorktreeRuntime()
        self.supervisor = ExecutionSupervisor()
        self.patch_engine = SafePatchEngine()

    def execute_task(self, task: dict):
        dgm_logger.info(f"AutonomousExecutor: Starting task {task.get('id')}")

        if not self.supervisor.validate_plan(task):
            dgm_logger.error("Execution rejected by supervisor")
            return False

        try:
            # Create sandbox
            worktree_path = self.runtime.create_sandbox(task.get('id'))

            # Execute logic (placeholder for agent interaction)
            dgm_logger.info(f"Executing in {worktree_path}")

            # Generate patch
            patch = self.patch_engine.generate_patch(worktree_path)

            # Validate patch
            if self.supervisor.authorize_commit(patch):
                self.patch_engine.apply_patch(patch)
                dgm_logger.info("Task executed and patch applied successfully")
                return True
        except Exception as e:
            dgm_logger.error(f"Execution failed: {e}")
            return False
        finally:
            self.runtime.cleanup_sandbox(task.get('id'))

        return False
