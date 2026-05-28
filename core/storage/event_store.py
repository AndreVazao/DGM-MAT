import json
import sqlite3
from core.storage.database import SessionLocal, engine
from core.storage.models import EventRecord, Base
from shared.models.event import Event
from core.observability.logger import dgm_logger

class EventStore:
    @staticmethod
    def persist(event: Event):
        # Ensure tables exist before first persist attempt
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            dgm_logger.error(f"EventStore: Failed to ensure schema: {e}")

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
        except Exception as e:
            dgm_logger.error(f"EventStore: Persist failed for {event.id}: {e}")
            db.rollback()
        finally:
            db.close()
