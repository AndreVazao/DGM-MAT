from typing import Dict, Any, List
from core.event_bus.bus import Event, EventBus

class GapDetector:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.gap_categories = [
            "missing_knowledge",
            "unknown_capability",
            "incomplete_agent_capability",
            "failed_operation_low_confidence",
            "unresolved_architectural_decision"
        ]
        # Subscribe to errors and low-confidence reports
        self.bus.subscribe("error", self._handle_error)
        self.bus.subscribe("task_failure", self._handle_error)

    def _handle_error(self, event: Event):
        category = event.payload.get("category")
        if category in self.gap_categories or event.payload.get("confidence", 1.0) < 0.5:
            self._trigger_gap_detection(event)

    def _trigger_gap_detection(self, source_event: Event):
        gap_context = {
            "source_event_id": source_event.id,
            "category": source_event.payload.get("category", "unknown_gap"),
            "agent_id": source_event.source,
            "description": source_event.payload.get("error") or source_event.payload.get("message"),
            "context": source_event.payload.get("context", {}),
            "trace_id": source_event.trace_id
        }

        self.bus.publish(Event(
            source="gap_detector",
            type="gap_detected",
            payload=gap_context,
            priority="high",
            trace_id=source_event.trace_id
        ))

        self._log(f"Knowledge gap detected: {gap_context['category']} from {gap_context['agent_id']}")

    def _log(self, message: str):
        self.bus.publish(Event(
            source="gap_detector",
            type="log",
            payload={"message": message, "category": "gap_detection"},
            priority="low"
        ))
