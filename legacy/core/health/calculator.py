from typing import Dict, Any, List
from core.event_bus.bus import Event, EventBus

class HealthCalculator:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.metrics: Dict[str, float] = {
            "agent_stability": 1.0,
            "repo_integrity": 1.0,
            "event_consistency": 1.0,
            "memory_drift": 0.0,
            "provider_reliability": 1.0,
            "deployment_success_rate": 1.0
        }

    def update_metric(self, metric_name: str, value: float):
        if metric_name in self.metrics:
            self.metrics[metric_name] = value
            self._publish_health_update()

    def calculate_global_score(self) -> float:
        """Calculate weighted global health score."""
        weights = {
            "agent_stability": 0.25,
            "repo_integrity": 0.2,
            "event_consistency": 0.15,
            "memory_drift": 0.1, # Inverse impact
            "provider_reliability": 0.15,
            "deployment_success_rate": 0.15
        }

        score = 0.0
        for metric, weight in weights.items():
            val = self.metrics[metric]
            if metric == "memory_drift":
                # High drift reduces health
                score += (1.0 - val) * weight
            else:
                score += val * weight

        return round(score, 2)

    def _publish_health_update(self):
        global_score = self.calculate_global_score()
        self.bus.publish(Event(
            source="health_calculator",
            type="health_update",
            payload={
                "global_score": global_score,
                "metrics": self.metrics
            },
            priority="medium"
        ))

    def get_status_report(self) -> Dict[str, Any]:
        return {
            "global_score": self.calculate_global_score(),
            "metrics": self.metrics,
            "status": "healthy" if self.calculate_global_score() > 0.8 else "unstable"
        }
