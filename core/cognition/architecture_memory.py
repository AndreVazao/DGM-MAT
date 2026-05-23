import json
import os
from datetime import datetime
from typing import List, Dict, Any
from core.cognition.cognition_snapshot import CognitionSnapshot

class ArchitectureMemory:
    def __init__(self, storage_path: str = "AndreOS/architecture_memory.json"):
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

    def record_evolution(self, snapshot: CognitionSnapshot):
        """Append-only recording of immutable snapshots."""
        record = {
            "version": len(self.history) + 1,
            "timestamp": datetime.now().isoformat(),
            "data": snapshot.model_dump()
        }
        self.history.append(record)

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)

    def rollback(self, version: int) -> Dict[str, Any]:
        """Returns a previous snapshot for manual rollback (read-only)."""
        for entry in self.history:
            if entry.get("version") == version:
                return entry["data"]
        return {}
