from typing import Any, Dict, List, Optional

from core.memory.memory_engine import MemoryEngine
from core.memory.memory_store import MemoryStore


class MemoryManager:
    def __init__(self):
        self.engine = MemoryEngine()
        self.store = MemoryStore()

    def store_memory(self, domain: str, content: Dict[str, Any], importance: float = 0.5):
        return self.engine.store_memory(domain, content, importance)

    def search_memory(self, query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.engine.search_memory(query, domain)

    def consolidate(self):
        return self.engine.consolidate()


memory_manager = MemoryManager()

__all__ = ["MemoryManager", "memory_manager"]
