from typing import Dict, Any, List
from core.autonomy.models import AutonomousTask
from core.observability.logger import dgm_logger

class PriorityEngine:
    """
    Advanced scoring engine for autonomous tasks with strategic and cognitive awareness.
    """
    def __init__(self):
        self.weights = {
            "severity": 0.3,
            "strategic_value": 0.3,
            "cognitive_impact": 0.2,
            "architectural_impact": 0.1,
            "confidence": 0.1
        }

    def calculate_score(self, task: AutonomousTask) -> int:
        """
        Calculates a dynamic priority score between 0 and 100.
        """
        score = 0.0

        # 1. Base Priority by Origin
        origin_scores = {
            "failed_execution": 90,
            "strategic_planner": 85,
            "repo_analysis": 60,
            "todo_scanner": 30,
            "security_scan": 95
        }
        base_score = origin_scores.get(task.origin, 20)

        # 2. Task Category Weighting
        category_multipliers = {
            "strategic": 1.4,
            "research": 1.2,
            "tactical": 1.0,
            "maintenance": 1.1,
            "self-improvement": 1.5
        }
        category = task.metadata.get("category", "tactical")
        cat_multiplier = category_multipliers.get(category, 1.0)

        # 3. Strategic and Cognitive Scoring (from metadata)
        strategic_value = task.metadata.get("strategic_impact", 0.5)
        cognitive_impact = task.metadata.get("cognitive_gain", 0.5)

        # 4. Final Weighted Calculation
        final_score = (
            (base_score * self.weights["severity"]) +
            (strategic_value * 100 * self.weights["strategic_value"]) +
            (cognitive_impact * 100 * self.weights["cognitive_impact"])
        ) * cat_multiplier

        # 5. Risk Adjustment
        risk_multipliers = {
            "CRITICAL": 1.3,
            "HIGH": 1.1,
            "MEDIUM": 1.0,
            "LOW": 0.9
        }
        risk_multiplier = risk_multipliers.get(task.risk, 1.0)

        final_score = int(min(100, final_score * risk_multiplier * task.confidence))

        dgm_logger.debug(f"PriorityEngine: Task {task.task_id} ({category}) scored {final_score}")
        return final_score

    def rank_tasks(self, tasks: List[AutonomousTask]) -> List[AutonomousTask]:
        """Returns tasks sorted by calculated priority."""
        for task in tasks:
            task.priority = self.calculate_score(task)
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
