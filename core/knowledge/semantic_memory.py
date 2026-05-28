import json
import os
from pathlib import Path
from typing import List, Optional
from core.knowledge.knowledge_models import SemanticSnapshot
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class SemanticMemory:
    def __init__(self, storage_path: Optional[str] = None):
        if not storage_path:
            # Phase 42.3-LITE: Persistent storage path
            self.storage_path = storage_manager.get_path("memory", "semantic_knowledge.json")
        else:
            self.storage_path = Path(storage_path)

        self.snapshots: List[SemanticSnapshot] = self._load()

    def _load(self) -> List[SemanticSnapshot]:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return [SemanticSnapshot(**s) for s in data]
            except Exception as exc:
                dgm_logger.error(f"SemanticMemory: Failed to load memory: {exc}")
        return []

    def persist(self, snapshot: SemanticSnapshot):
        self.snapshots.append(snapshot)
        # Keep history limited to prevent infinite growth in this phase
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump([s.model_dump(mode='json') for s in self.snapshots], f, indent=2)
            dgm_logger.info(f"SemanticMemory: Snapshot {snapshot.id} persisted to {self.storage_path}")
        except Exception as exc:
            dgm_logger.error(f"SemanticMemory: Failed to persist memory: {exc}")

    def get_latest(self) -> Optional[SemanticSnapshot]:
        return self.snapshots[-1] if self.snapshots else None
