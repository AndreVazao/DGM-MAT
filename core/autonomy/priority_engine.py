from typing import Dict, Any, List
from core.autonomy.models import AutonomousTask
from core.observability.logger import dgm_logger

class PriorityEngine:
    """
    Advanced scoring engine for autonomous tasks.
    """
    def __init__(self):
        self.weights = {
            "severity": 0.4,
            "architectural_impact": 0.2,
            "duplication_reduction": 0.1,
            "runtime_stability": 0.1,
            "confidence": 0.1,
            "repo_criticality": 0.1
        }

    def calculate_score(self, task: AutonomousTask) -> int:
        """
        Calculates a dynamic priority score between 0 and 100.
        """
        score = 0

        # 1. Base Priority by Origin
        origin_scores = {
            "failed_execution": 90,
            "repo_analysis": 60,
            "todo_scanner": 30,
            "provider_sync": 40,
            "security_scan": 95
        }
        base_score = origin_scores.get(task.origin, 20)

        # 2. Risk Adjustment
        risk_multipliers = {
            "CRITICAL": 1.5,
            "HIGH": 1.2,
            "MEDIUM": 1.0,
            "LOW": 0.8
        }
        multiplier = risk_multipliers.get(task.risk, 1.0)

        # 3. Confidence Factor
        confidence_factor = task.confidence

        # 4. Final Calculation
        final_score = int(min(100, base_score * multiplier * confidence_factor))

        dgm_logger.debug(f"PriorityEngine: Task {task.task_id} scored {final_score}")
        return final_score

    def rank_tasks(self, tasks: List[AutonomousTask]) -> List[AutonomousTask]:
        """Returns tasks sorted by calculated priority."""
        for task in tasks:
            task.priority = self.calculate_score(task)
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
