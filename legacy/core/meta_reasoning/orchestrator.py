from typing import Dict, Any, List
from core.event_bus.bus import Event, EventBus

class MetaReasoningOrchestrator:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.pending_retries: Dict[str, Event] = {} # trace_id -> original_task_event
        self.bus.subscribe("knowledge_integrated", self._handle_knowledge_integrated)
        self.bus.subscribe("gap_detected", self._track_gap)

    def _track_gap(self, event: Event):
        # We need the original task to retry it later.
        # In this implementation, we assume the trace_id links them.
        # Real implementation would need a more robust way to capture the original task context.
        pass

    def register_task_for_retry(self, trace_id: str, task_event: Event):
        self.pending_retries[trace_id] = task_event
        self._log(f"Task {task_event.id} registered for retry after knowledge integration (Trace: {trace_id})")

    def _handle_knowledge_integrated(self, event: Event):
        trace_id = event.trace_id
        if trace_id in self.pending_retries:
            original_task = self.pending_retries.pop(trace_id)
            self._log(f"Knowledge integrated for Trace {trace_id}. Retrying original task {original_task.id}.")

            # Re-publish the original task with a 'retry' flag
            retry_payload = original_task.payload.copy()
            retry_payload["is_retry"] = True
            retry_payload["new_knowledge"] = event.payload.get("solution")

            self.bus.publish(Event(
                source="meta_reasoning",
                target=original_task.target,
                type="task",
                payload=retry_payload,
                priority=original_task.priority,
                trace_id=trace_id
            ))

    def _log(self, message: str):
        self.bus.publish(Event(
            source="meta_reasoning",
            type="log",
            payload={"message": message, "category": "meta_reasoning"},
            priority="low"
        ))
