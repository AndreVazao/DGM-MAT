import json
import os
from typing import List, Optional
from core.knowledge.knowledge_models import SemanticSnapshot
from core.observability.logger import dgm_logger

class SemanticMemory:
    def __init__(self, storage_path: str = "AndreOS/semantic_knowledge.json"):
        self.storage_path = storage_path
        self.snapshots: List[SemanticSnapshot] = self._load()

    def _load(self) -> List[SemanticSnapshot]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return [SemanticSnapshot(**s) for s in data]
            except Exception as exc:
                dgm_logger.error(f"SemanticMemory: Failed to load memory: {exc}")
        return []

    def persist(self, snapshot: SemanticSnapshot):
        self.snapshots.append(snapshot)
        # Keep it append-only and limited for this phase
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump([s.model_dump(mode='json') for s in self.snapshots], f, indent=2)
            dgm_logger.info(f"SemanticMemory: Snapshot {snapshot.id} persisted.")
        except Exception as exc:
            dgm_logger.error(f"SemanticMemory: Failed to persist memory: {exc}")

    def get_latest(self) -> Optional[SemanticSnapshot]:
        return self.snapshots[-1] if self.snapshots else None
