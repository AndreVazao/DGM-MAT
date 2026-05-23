import json
import os
from datetime import datetime
from typing import List, Dict, Any

class RecoveryMemory:
    def __init__(self, storage_path: str = "AndreOS/recovery_memory.json"):
        self.storage_path = storage_path
        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def record_recovery(self, crash_type: str, status: str):
        """Append-only recovery logs."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "crash_type": crash_type,
            "status": status,
            "id": len(self.history) + 1
        }
        self.history.append(record)

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=2)
