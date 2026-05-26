import time
import json
from typing import Dict, Any, List
from pathlib import Path
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class MetricsCollector:
    def __init__(self):
        self.storage_path = storage_manager.get_path("telemetry")
        self.metrics_file = self.storage_path / "runtime_metrics.json"
        self.buffer: List[Dict[str, Any]] = []

    def collect(self, metric_type: str, value: Any, metadata: Dict[str, Any] = None):
        metric = {
            "timestamp": time.time(),
            "type": metric_type,
            "value": value,
            "metadata": metadata or {}
        }
        self.buffer.append(metric)
        if len(self.buffer) >= 10:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        dgm_logger.debug(f"MetricsCollector: Flushing {len(self.buffer)} metrics to disk.")
        # Simplified: append to file (in reality use a database or specialized storage)
        existing = []
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    existing = json.load(f)
            except:
                pass

        existing.extend(self.buffer)
        with open(self.metrics_file, "w") as f:
            json.dump(existing[-1000:], f, indent=2) # Keep last 1000
        self.buffer = []
