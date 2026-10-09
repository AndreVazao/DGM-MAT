from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class ExecutionDirector:
    """Planning-only director until a real execution adapter is connected.

    Never report validation merely because an objective received a placeholder ID.
    """

    def assign_tasks(self, objectives: List[Dict[str, Any]]) -> List[str]:
        dgm_logger.info(
            "ExecutionDirector: Creating planning placeholders for %s objectives; no worker execution is wired.",
            len(objectives),
        )
        return [f"planned_task_{i}" for i in range(len(objectives))]

    def validate_execution(self, task_ids: List[str]) -> Dict[str, Any]:
        """Report truthfully that no execution evidence exists yet."""
        dgm_logger.warning(
            "ExecutionDirector: Cannot validate %s tasks because no execution adapter is wired.",
            len(task_ids),
        )
        return {task_id: "NOT_EXECUTED" for task_id in task_ids}
