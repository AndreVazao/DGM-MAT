from shared.models.event import Event
from core.realtime.realtime_broadcast import (
    safe_broadcast,
)

def stream_event(event: Event):
    safe_broadcast(
        {
            "type": "event",
            "event_type": event.event_type,
            "source": event.source,
            "target": event.target,
            "trace_id": event.trace_id,
            "payload": event.payload,
        }
    )
