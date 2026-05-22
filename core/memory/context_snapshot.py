from datetime import datetime
from uuid import uuid4

from core.memory.models import (
    MemoryRecord,
)

from core.memory.memory_store import (
    MemoryStore,
)


class ContextSnapshot:

    def create(
        self,
        content: str,
        tags: list[str],
    ):

        memory = MemoryRecord(
            memory_id=str(uuid4()),
            category="snapshot",
            content=content,
            source="runtime",
            timestamp=datetime.now(),
            tags=tags,
        )

        MemoryStore().save(memory)
