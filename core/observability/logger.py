import json
import datetime
from typing import Optional
from core.event_bus.bus import Event, EventBus

class EventLogger:
    def __init__(self, event_bus: EventBus, log_file: Optional[str] = None):
        self.bus = event_bus
        self.log_file = log_file

        # Subscribe to all event types for comprehensive logging
        self.bus.subscribe("*", self.log_event)

    def log_event(self, event: Event):
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_id": event.id,
            "type": event.type,
            "source": event.source,
            "target": event.target,
            "priority": event.priority,
            "trace_id": event.trace_id,
            "payload": event.payload
        }

        log_str = json.dumps(log_entry)

        # Internal console log (event-driven)
        if event.type == "log":
            print(f"[LOG] [{event.source}] {event.payload.get('message')}")
        elif event.type == "error":
            print(f"[CRITICAL ERROR] [{event.source}] {event.payload}")
        elif event.type == "heartbeat":
            # Silent heartbeats unless debugging
            pass
        else:
            # General event trace
            pass

        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log_str + "\n")

    def log_validation_failure(self, event: Event, reason: str):
        error_event = Event(
            source="validation_engine",
            type="error",
            payload={"event_id": event.id, "reason": reason, "context": "validation_failure"},
            priority="critical"
        )
        self.bus.publish(error_event)
