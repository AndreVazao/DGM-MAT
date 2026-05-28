from typing import Dict, Any, List
from core.autonomy.models import AutonomousTask
from core.observability.logger import dgm_logger

class PriorityEngine:
    """
    Advanced scoring engine for autonomous tasks with strategic and cognitive awareness.
    Hardened for critical runtime stabilization and strategic evolution.
    """
    def __init__(self):
        # Base component weights
        self.weights = {
            "severity": 0.4,
            "strategic": 0.3,
            "cognitive": 0.3
        }

    def calculate(self, issue_type: str) -> int:
        """Legacy support for issue type scoring."""
        mapping = {
            "bug": 80,
            "feature": 50,
            "refactor": 40,
            "docs": 20,
            "security": 95
        }
        return mapping.get(issue_type.lower(), 30)

    def calculate_score(self, task: AutonomousTask) -> int:
        """
        Calculates a dynamic priority score between 0 and 100.
        Prioritizes failed executions and high-risk core system tasks.
        """
        # 1. Map Origin to Severity Score
        origin_scores = {
            "failed_execution": 95,
            "strategic_planner": 85,
            "security_scan": 95,
            "repo_analysis": 60,
            "todo_scanner": 30,
            "manual": 50
        }
        severity_score = origin_scores.get(task.origin, 40)

        # 2. Extract Strategic and Cognitive Metrics
        strategic_value = task.metadata.get("strategic_impact", 0.5) * 100
        cognitive_impact = task.metadata.get("cognitive_gain", 0.5) * 100

        # 3. Category Elevators (Core Systems get baseline strategic value)
        category = task.metadata.get("category", "tactical")
        core_categories = ["runtime", "infrastructure", "autonomy", "self-improvement"]
        if category in core_categories or any(c in str(task.repo).lower() for c in core_categories):
            strategic_value = max(strategic_value, 80)

        # 4. Weighted Base Score
        base_score = (
            (severity_score * self.weights["severity"]) +
            (strategic_value * self.weights["strategic"]) +
            (cognitive_impact * self.weights["cognitive"])
        )

        # Factor in initial priority (0-100 range)
        input_priority = max(0, min(100, task.priority))
        combined_base = (base_score * 0.85) + (input_priority * 0.15)

        # 5. Critical Boost Multipliers (Additive logic for compound importance)
        multiplier = 1.0

        if task.origin == "failed_execution":
            multiplier += 0.5  # Critical stabilization boost

        if task.risk == "HIGH":
            multiplier += 0.3
        elif task.risk == "CRITICAL":
            multiplier += 0.6

        if category == "strategic":
            multiplier += 0.2
        elif category == "self-improvement":
            multiplier += 0.3
        elif category == "research":
            multiplier += 0.1

        # 6. Final Calculation with Confidence and Cap
        final_score = int(min(100, combined_base * multiplier * task.confidence))

        dgm_logger.debug(f"PriorityEngine: Task {task.task_id} ({category}) scored {final_score}")
        return final_score

    def rank_tasks(self, tasks: List[AutonomousTask]) -> List[AutonomousTask]:
        """Returns tasks sorted by calculated priority."""
        for task in tasks:
            task.priority = self.calculate_score(task)
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
