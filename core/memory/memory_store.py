import json
from pathlib import Path

from core.memory.models import (
    MemoryRecord,
)


MEMORY_PATH = Path(
    "C:/DevopsGodMode/data/memory"
)

MEMORY_PATH.mkdir(
    parents=True,
    exist_ok=True,
)


class MemoryStore:

    def save(
        self,
        memory: MemoryRecord,
    ):

        filename = (
            MEMORY_PATH /
            f"{memory.memory_id}.json"
        )

        data = {
            "memory_id": memory.memory_id,
            "category": memory.category,
            "content": memory.content,
            "source": memory.source,
            "timestamp": (
                memory.timestamp.isoformat()
            ),
            "tags": memory.tags,
        }

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )
