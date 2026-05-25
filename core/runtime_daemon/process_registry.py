import os
import json
import time
from pathlib import Path
from typing import Dict, Optional
from core.observability.logger import dgm_logger

class ProcessRegistry:
    """
    Hardened process registry with atomic writes and corruption protection.
    """
    def __init__(self, registry_path: str = ".runtime/process_registry.json"):
        self.path = Path(registry_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def register_self(self, process_name: str = "daemon"):
        pid = os.getpid()
        data = self._load()
        data[process_name] = {
            "pid": pid,
            "started_at": time.time()
        }
        self._save(data)
        dgm_logger.info(f"ProcessRegistry: Registered {process_name} (PID: {pid})")

    def unregister(self, process_name: str = "daemon"):
        data = self._load()
        if process_name in data:
            del data[process_name]
            self._save(data)

    def get_pid(self, process_name: str) -> Optional[int]:
        return self._load().get(process_name, {}).get("pid")

    def _load(self) -> dict:
        if not self.path.exists(): return {}
        try:
            content = self.path.read_text()
            if not content: return {}
            return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            dgm_logger.error(f"ProcessRegistry: Malformed registry detected: {e}")
            return {}

    def _save(self, data: dict):
        try:
            temp_file = self.path.with_suffix(".tmp")
            temp_file.write_text(json.dumps(data, indent=2))
            temp_file.replace(self.path)
        except Exception as e:
            dgm_logger.error(f"ProcessRegistry: Atomic save failed: {e}")
