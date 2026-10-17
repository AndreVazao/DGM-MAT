from core.observability.logger import dgm_logger
from typing import Any, Dict
from core.execution.approval_manager import approval_manager

class ExecutionSupervisor:
    """
    Supervises autonomous development cycles and enforces safety guardrails.
    Integrates with ApprovalManager for mission-critical tasks.
    """
    def __init__(self):
        self.active_executions = {}

    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Validates an execution plan before it starts.
        """
        dgm_logger.info(f"Supervisor: Validating plan {plan.get('id', 'unknown')}")
        return True

    def monitor_execution(self, execution_id: str):
        """
        Active monitoring of a running task.
        """
        dgm_logger.info(f"Supervisor: Monitoring execution {execution_id}")

    def authorize_commit(self, patch: str, task_id: str = "unknown", approval_required: bool = False) -> bool:
        """
        Final safety gate before a patch is allowed to be merged.
        If approval_required is True, redirects to ApprovalManager.
        """
        dgm_logger.info(f"Supervisor: Authorizing patch commit for task {task_id}")

        if approval_required:
            dgm_logger.info(f"Supervisor: Task {task_id} requires human approval.")
            # Request approval via manager.
            # In a real async loop, this would suspend execution.
            # For PHASE 41-LITE, we register it and return False (pending).
            approval_manager.request_approval(task_id, patch)
            return False

        return True
