import json
import time
from typing import Dict, Any, List
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class RuntimeMetrics:
    """
    Collects and persists system-wide runtime metrics.
    """
    def __init__(self, registry):
        self.registry = registry
        self.storage_path = storage_manager.get_path("logs", "runtime_metrics.jsonl")
        self.last_capture = 0

    @property
    def name(self) -> str:
        return "metrics"

    def start(self) -> bool:
        return True

    def stop(self) -> bool:
        return True

    def capture_snapshot(self):
        self.last_capture = time.time()
        snapshot = {
            "timestamp": self.last_capture,
            "services": self.registry.get_metrics_report()
        }
        self._persist_snapshot(snapshot)

    def _persist_snapshot(self, snapshot: Dict[str, Any]):
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot) + "\n")
        except Exception as e:
            dgm_logger.error(f"RuntimeMetrics: Failed to persist snapshot: {e}")

    def health(self) -> Dict[str, Any]:
        return {
            "metrics_file": str(self.storage_path),
            "last_capture": self.last_capture
        }

    def metrics(self) -> Dict[str, Any]:
        return {}
