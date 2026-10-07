import json
from core.storage.database import SessionLocal
from core.storage.models import EventRecord
from core.storage.init_db import init_database
from core.contracts.compat import event_to_contract
from dgm_contracts import EventEnvelope
from shared.models.event import Event
from core.observability.logger import dgm_logger

class EventStore:
    @staticmethod
    def persist(event: Event) -> EventEnvelope:
        init_database()
        envelope=event_to_contract(event)
        db=SessionLocal()
        try:
            existing=db.query(EventRecord).filter(EventRecord.event_id==event.id).first()
            serialized=envelope.model_dump_json()
            if existing:
                existing.envelope_json=serialized
                existing.payload=json.dumps(event.payload)
                existing.trace_id=event.trace_id
            else:
                db.add(EventRecord(event_id=event.id,source=event.source,target=event.target,
                    event_type=event.event_type,payload=json.dumps(event.payload),
                    trace_id=event.trace_id,envelope_json=serialized))
            db.commit()
            return envelope
        except Exception as e:
            db.rollback()
            dgm_logger.error(f"EventStore: Persist failed for {event.id}: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def replay(limit:int=100,event_type:str|None=None)->list[EventEnvelope]:
        init_database();db=SessionLocal()
        try:
            q=db.query(EventRecord).order_by(EventRecord.id.asc())
            if event_type:q=q.filter(EventRecord.event_type==event_type)
            result=[]
            for r in q.limit(limit).all():
                if r.envelope_json:
                    result.append(EventEnvelope.model_validate_json(r.envelope_json))
                else:
                    result.append(EventEnvelope(event_id=r.event_id,source=r.source,target=r.target,
                        event_type=r.event_type,payload=json.loads(r.payload or "{}"),trace_id=r.trace_id))
            return result
        finally: db.close()

    @staticmethod
    def get(event_id:str)->EventEnvelope|None:
        init_database();db=SessionLocal()
        try:
            r=db.query(EventRecord).filter(EventRecord.event_id==event_id).first()
            if not r:return None
            if r.envelope_json:return EventEnvelope.model_validate_json(r.envelope_json)
            return EventEnvelope(event_id=r.event_id,source=r.source,target=r.target,
                event_type=r.event_type,payload=json.loads(r.payload or "{}"),trace_id=r.trace_id)
        finally: db.close()
