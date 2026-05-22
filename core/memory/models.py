from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryRecord:

    memory_id: str

    category: str

    content: str

    source: str

    timestamp: datetime

    tags: list[str]
