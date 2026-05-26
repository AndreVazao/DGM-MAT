import json
from pathlib import Path
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class StrategicMemory:
    def __init__(self):
        self.storage_path = storage_manager.get_path("memory") / "strategic_context.json"

    def record_decision(self, context: str, decision: str):
        data = self._load()
        data.append({"timestamp": "...", "context": context, "decision": decision})
        self._save(data)

    def _load(self):
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return []

    def _save(self, data):
        self.storage_path.write_text(json.dumps(data, indent=2))
