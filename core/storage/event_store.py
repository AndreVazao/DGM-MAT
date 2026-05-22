import json
from core.storage.database import SessionLocal
from core.storage.models import EventRecord
from shared.models.event import Event

class EventStore:
    @staticmethod
    def persist(event: Event):
        db = SessionLocal()
        try:
            record = EventRecord(
                event_id=event.id,
                source=event.source,
                target=event.target,
                event_type=event.event_type,
                payload=json.dumps(event.payload),
                trace_id=event.trace_id,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()
