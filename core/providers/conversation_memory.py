from datetime import datetime
from uuid import uuid4

from core.memory.memory_store import (
    MemoryStore,
)

from core.memory.models import (
    MemoryRecord,
)

from core.providers.models.conversation import (
    Conversation,
)


class ConversationMemory:

    def persist(
        self,
        conversations: list[Conversation],
    ):

        for convo in conversations:

            memory = MemoryRecord(
                memory_id=str(uuid4()),
                category="conversation",
                content=(
                    f"{convo.provider} | "
                    f"{convo.title}"
                ),
                source=convo.provider,
                timestamp=datetime.now(),
                tags=convo.tags,
            )

            MemoryStore().save(memory)
