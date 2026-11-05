from datetime import datetime, timedelta, timezone
from typing import List

from core.knowledge.knowledge_models import KnowledgeNode


class TemporalMemory:
    def __init__(self):
        self.history: List[KnowledgeNode] = []

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime:
        """Normalize mixed naive/aware event timestamps before comparison.

        Legacy events may carry naive datetimes; treat those as UTC so startup
        ingestion remains deterministic across local and frozen runtimes.
        """
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def add(self, node: KnowledgeNode):
        self.history.append(node)
        now = datetime.now(timezone.utc)
        self.history = [
            item for item in self.history
            if now - self._as_utc(item.timestamp) < timedelta(days=30)
        ]

    def get_recent(self, hours: int = 24) -> List[KnowledgeNode]:
        now = datetime.now(timezone.utc)
        return [
            item for item in self.history
            if now - self._as_utc(item.timestamp) < timedelta(hours=hours)
        ]
