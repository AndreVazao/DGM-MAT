import uuid
import datetime
import heapq
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field, asdict

PRIORITY_MAP = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3
}

@dataclass(order=True)
class Event:
    priority_val: int = field(init=False)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    source: str = ""
    target: str = "broadcast"
    type: str = "update"
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"
    ecosystem: str = "DGM-MAT"
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        self.priority_val = PRIORITY_MAP.get(self.priority.lower(), 2)

    def to_dict(self):
        return asdict(self)

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self.queue = [] # Priority queue (min-heap)
        self._validation_engine = None

    def set_validation_engine(self, engine):
        self._validation_engine = engine

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event: Event):
        # 1. Validation Layer
        if self._validation_engine:
            if not self._validation_engine.validate_event(event):
                self._log_event_failure(event, "Validation Failed")
                return False

        # 2. Malformed check (basic)
        if not event.id or not event.source:
            self._log_event_failure(event, "Malformed Event: Missing ID or Source")
            return False

        # 3. Queue handling (Priority)
        heapq.heappush(self.queue, event)

        # 4. Immediate Routing (In this minimal implementation)
        self._route_event(event)
        return True

    def _route_event(self, event: Event):
        # Notify specific type subscribers
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                callback(event)

        # Notify "all" or "broadcast" subscribers if any
        if "*" in self.subscribers:
            for callback in self.subscribers["*"]:
                callback(event)

    def _log_event_failure(self, event: Event, reason: str):
        # This will be replaced by event-driven observability later
        print(f"[EVENT BUS ERROR] {reason}: {event.id} ({event.type})")

    def process_queue(self):
        """Process one event from the priority queue."""
        if self.queue:
            event = heapq.heappop(self.queue)
            self._route_event(event)
            return event
        return None
