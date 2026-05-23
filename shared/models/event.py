from datetime import datetime
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from shared.enums.event_priority import EventPriority

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str
    target: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: EventPriority = EventPriority.LOW
    ecosystem: str = "core"
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_trace_id: Optional[str] = None
    depth: int = 0
