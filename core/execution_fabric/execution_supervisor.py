from __future__ import annotations

import math
import re
from typing import Any, Dict

from core.observability.logger import dgm_logger
from core.execution.approval_manager import approval_manager


_TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_FORBIDDEN_EXECUTION_FIELDS = {"command", "commands", "shell", "script", "executable", "argv"}


class ExecutionSupervisor:
    """Validate task metadata and persist approval requests for risky changes."""

    def __init__(self):
        self.active_executions: dict[str, dict[str, Any]] = {}

    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """Reject malformed plans and caller-supplied executable instructions."""
        if not isinstance(plan, dict):
            dgm_logger.warning("Supervisor: Rejected plan because it is not a mapping.")
            return False
        task_id = plan.get("id")
        objective = plan.get("goal") or plan.get("description") or plan.get("summary")
        if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
            dgm_logger.warning("Supervisor: Rejected plan with missing or invalid task ID.")
            return False
        if not isinstance(objective, str) or not objective.strip():
            dgm_logger.warning(f"Supervisor: Rejected task {task_id}: objective is required.")
            return False
        if _FORBIDDEN_EXECUTION_FIELDS.intersection(plan):
            dgm_logger.warning(f"Supervisor: Rejected task {task_id}: executable fields are not accepted.")
            return False
        if "approval_required" in plan and not isinstance(plan["approval_required"], bool):
            dgm_logger.warning(f"Supervisor: Rejected task {task_id}: approval_required must be boolean.")
            return False
        dgm_logger.info(f"Supervisor: Validated bounded task metadata for {task_id}.")
        return True

    def monitor_execution(self, execution_id: str):
        dgm_logger.info(f"Supervisor: Monitoring execution {execution_id}")

    def authorize_commit(
        self,
        patch: str,
        task_id: str = "unknown",
        approval_required: bool = False,
        risk_score: float = 0.0,
        impact: str = "LOW",
    ) -> bool:
        """Persist a human approval request when policy or patch risk requires it.

        A True result means the patch may remain in its isolated worktree; it does
        not authorize merging, committing to the primary branch, or deployment.
        """
        if not isinstance(patch, str) or not patch.strip():
            return False
        if (
            isinstance(risk_score, bool)
            or not isinstance(risk_score, (int, float))
            or not math.isfinite(float(risk_score))
            or not 0.0 <= float(risk_score) <= 1.0
            or not isinstance(approval_required, bool)
            or not isinstance(impact, str)
            or impact not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        ):
            return False
        if approval_required:
            if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
                return False
            dgm_logger.warning(f"Supervisor: Task {task_id} requires human approval.")
            approval_manager.request_approval(task_id, patch, risk_score, impact)
            return False
        return True
