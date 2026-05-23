from typing import Dict, List, Set
from shared.models.event import Event
from core.observability.logger import dgm_logger

class LoopDetector:
    def __init__(self):
        self.trace_chains: Dict[str, List[str]] = {} # trace_id -> list of event_types

    def detect_loop(self, event: Event) -> bool:
        """Returns True if a potential loop is detected."""
        if not event.trace_id:
            return False

        if event.trace_id not in self.trace_chains:
            self.trace_chains[event.trace_id] = []

        chain = self.trace_chains[event.trace_id]

        # Simple heuristic: if the same event type appears too many times in the same trace
        if chain.count(event.event_type) > 5:
            dgm_logger.warning(f"LoopDetector: Potential loop detected for trace {event.trace_id} with event type {event.event_type}")
            return True

        chain.append(event.event_type)

        # Trim chain if it gets too long
        if len(chain) > 50:
            self.trace_chains[event.trace_id] = chain[-50:]

        return False

    def clear_trace(self, trace_id: str):
        if trace_id in self.trace_chains:
            del self.trace_chains[trace_id]
