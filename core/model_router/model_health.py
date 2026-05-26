from typing import Dict
from core.observability.logger import dgm_logger

class ModelHealthTracker:
    def __init__(self):
        self.health_stats = {}

    def report_success(self, model_id: str):
        stats = self.health_stats.get(model_id, {"success": 0, "failure": 0})
        stats["success"] += 1
        self.health_stats[model_id] = stats

    def report_failure(self, model_id: str):
        stats = self.health_stats.get(model_id, {"success": 0, "failure": 0})
        stats["failure"] += 1
        self.health_stats[model_id] = stats
