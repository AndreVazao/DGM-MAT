from typing import Dict, List
from shared.models.event import Event
from shared.enums.event_priority import EventPriority

class QueueBalancer:
    def __init__(self):
        self.priority_weights = {
            EventPriority.CRITICAL: 10,
            EventPriority.HIGH: 5,
            EventPriority.MEDIUM: 2,
            EventPriority.LOW: 1
        }

    def balance_queues(self, events: List[Event]) -> List[Event]:
        # Weighted sorting
        return sorted(
            events,
            key=lambda e: self.priority_weights.get(e.priority, 1),
            reverse=True
        )
