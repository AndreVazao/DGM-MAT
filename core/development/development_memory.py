import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.storage.storage_manager import storage_manager

class DevelopmentMemory:
    def __init__(self, storage_path: Optional[str] = None):
        if not storage_path:
            self.storage_path = storage_manager.get_path("memory", "development_memory.json")
        else:
            self.storage_path = Path(storage_path)

        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def record_feature(self, feature_id: str, status: str):
        """Append-only implementation logs."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "feature_id": feature_id,
            "status": status,
            "snapshot_id": len(self.history) + 1
        }
        self.history.append(record)

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=2)
