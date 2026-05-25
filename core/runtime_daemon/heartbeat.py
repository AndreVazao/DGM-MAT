import json
import time
import os
from pathlib import Path
from datetime import datetime
from core.observability.logger import dgm_logger

class HeartbeatManager:
    def __init__(self, heartbeat_path: str = ".runtime/heartbeat.json"):
        self.path = Path(heartbeat_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def pulse(self, status: str = "running", metadata: dict = None):
        data = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "status": status,
            "metadata": metadata or {}
        }
        try:
            temp_path = self.path.with_suffix(".tmp")
            temp_path.write_text(json.dumps(data, indent=2))
            temp_path.replace(self.path)
        except Exception as e:
            dgm_logger.error(f"HeartbeatManager: Failed to write heartbeat: {e}")

    def get_last_pulse(self) -> dict:
        if not self.path.exists(): return {}
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}
