import json
from typing import Optional
from core.memory.models import MemoryRecord
from core.storage.storage_manager import storage_manager

class MemoryStore:
    def __init__(self):
        self.storage = storage_manager

    def save(self, memory: MemoryRecord):
        """Saves a memory record using the centralized storage manager."""
        filename = f"{memory.memory_id}.json"

        data = {
            "memory_id": memory.memory_id,
            "category": memory.category,
            "content": memory.content,
            "source": memory.source,
            "timestamp": memory.timestamp.isoformat(),
            "tags": memory.tags,
        }

        content = json.dumps(data, indent=2, ensure_ascii=False)
        self.storage.save_data("memory", filename, content)

    def load(self, memory_id: str) -> Optional[MemoryRecord]:
        """Loads a memory record from storage."""
        content = self.storage.read_data("memory", f"{memory_id}.json")
        if not content:
            return None

        return content
