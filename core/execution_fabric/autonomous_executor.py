from core.observability.logger import dgm_logger
from core.execution_fabric.worktree_runtime import WorktreeRuntime
from core.execution_fabric.execution_supervisor import ExecutionSupervisor
from core.execution_fabric.safe_patch_engine import SafePatchEngine


class AutonomousExecutor:
    """Prepare changes in a registered worktree; never patch the primary checkout."""

    def __init__(self):
        self.runtime = WorktreeRuntime()
        self.supervisor = ExecutionSupervisor()
        self.patch_engine = SafePatchEngine()

    def execute_task(self, task: dict):
        if not self.supervisor.validate_plan(task):
            dgm_logger.error("Execution rejected by supervisor.")
            return False

        task_id = task["id"]
        dgm_logger.info(f"AGENT_DISPATCHED: Task {task_id}")
        created_sandbox = False
        try:
            worktree_path = self.runtime.create_sandbox(task_id)
            if worktree_path is None:
                dgm_logger.error(f"Execution stopped: isolated worktree unavailable for {task_id}.")
                return False
            created_sandbox = True

            # The implementation/provider stage is deliberately not simulated here.
            # A future implementation adapter must make changes inside this worktree.
            patch = self.patch_engine.generate_patch(worktree_path)
            if not patch.strip():
                dgm_logger.warning(f"Task {task_id} produced no code changes; refusing to report success.")
                return False

            risk_info = self.patch_engine.assess_risk(patch)
            approval_required = (
                task.get("approval_required", False)
                or risk_info["level"] in {"HIGH", "CRITICAL"}
                or risk_info["is_blocked"]
            )

            if not self.supervisor.authorize_commit(
                patch,
                task_id,
                approval_required,
                risk_score=risk_info["score"],
                impact=risk_info["level"],
            ):
                dgm_logger.warning(
                    f"Task {task_id} is awaiting human approval. "
                    f"Changes remain in the isolated worktree: {worktree_path}"
                )
                return False

            # The diff already exists in the worktree. Re-applying it would be
            # incorrect; merging/committing is intentionally outside this executor.
            dgm_logger.info(
                f"Task {task_id} prepared changes in {worktree_path}; "
                "independent QA and explicit integration are still required."
            )
            return False

        except Exception as exc:
            dgm_logger.error(f"Execution failed for {task_id}: {exc}")
            return False
        finally:
            # WorktreeRuntime removes only clean worktrees. Dirty work, including
            # approval-pending changes, is preserved for inspection and recovery.
            if created_sandbox:
                self.runtime.cleanup_sandbox(task_id)
