import psutil
from typing import Dict, Any

class CockpitMetrics:
    def get_current_stats(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "tasks_pending": 0, # Placeholder
            "cognition_cycle_time": 0.0 # Placeholder
        }
