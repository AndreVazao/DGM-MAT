import json
import time
from pathlib import Path
from typing import Dict, Any
from core.observability.logger import dgm_logger
from core.storage.storage_manager import storage_manager

class MetricsCollector:
    def __init__(self):
        self.telemetry_dir = storage_manager.get_path("temp") / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

    def record_event(self, domain: str, event_type: str, data: Dict[str, Any]):
        timestamp = int(time.time())
        payload = {"timestamp": timestamp, "domain": domain, "event_type": event_type, "data": data}
        try:
            target_path = Path(".runtime") / domain / f"{domain}_{event_type}_{timestamp}.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception: pass

    def collect(self, metric_name: str, value: Any):
        """Legacy compatibility for collect() method."""
        self.record_event("telemetry", "metric", {metric_name: value})

metrics_collector = MetricsCollector()
