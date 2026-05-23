import json
import os
from datetime import datetime
from typing import List, Dict, Any
from core.cognition.cognition_snapshot import CognitionSnapshot
from core.storage.storage_manager import RuntimeStorageManager

class ArchitectureMemory:
    def __init__(self, storage_manager: RuntimeStorageManager = None):
        self.storage_manager = storage_manager or RuntimeStorageManager()
        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        content = self.storage_manager.read_data("cognition", "architecture_memory.json")
        if content:
            try:
                self.history = json.loads(content)
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

        self.storage_manager.save_data(
            "cognition",
            "architecture_memory.json",
            json.dumps(self.history, indent=2, default=str)
        )

    def rollback(self, version: int) -> Dict[str, Any]:
        """Returns a previous snapshot for manual rollback (read-only)."""
        for entry in self.history:
            if entry.get("version") == version:
                return entry["data"]
        return {}
