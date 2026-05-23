from datetime import datetime, timedelta
from typing import List
from core.knowledge.knowledge_models import KnowledgeNode

class TemporalMemory:
    def __init__(self):
        self.history: List[KnowledgeNode] = []

    def add(self, node: KnowledgeNode):
        self.history.append(node)
        # Prune old history (keep 30 days)
        now = datetime.now()
        self.history = [n for n in self.history if now - n.timestamp < timedelta(days=30)]

    def get_recent(self, hours: int = 24) -> List[KnowledgeNode]:
        now = datetime.now()
        return [n for n in self.history if now - n.timestamp < timedelta(hours=hours)]
