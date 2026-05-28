import json
import threading
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Column
from core.storage.database import Base, engine, SessionLocal
from core.observability.logger import dgm_logger

class ActionStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUEUED = "QUEUED"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"

class ActionRecord(Base):
    __tablename__ = "safe_action_queue"

    id = Column(Integer, primary_key=True)
    action_type = Column(String(255))
    payload = Column(Text)
    status = Column(String(50), default=ActionStatus.DISCOVERED)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    audit_trail = Column(Text, default="[]")
    error_message = Column(Text, nullable=True)

class SafeActionQueue:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SafeActionQueue, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Ensure table exists
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            dgm_logger.warning(f"SafeActionQueue: Early DB init failed (expected during build): {e}")
        self._initialized = True
        dgm_logger.info("SafeActionQueue: Initialized.")

    def enqueue(self, action_type: str, payload: Dict[str, Any]) -> int:
        with SessionLocal() as session:
            action = ActionRecord(
                action_type=action_type,
                payload=json.dumps(payload),
                status=ActionStatus.QUEUED,
                audit_trail=json.dumps([{
                    "timestamp": datetime.now().isoformat(),
                    "status": ActionStatus.QUEUED,
                    "message": "Action enqueued"
                }])
            )
            session.add(action)
            session.commit()
            session.refresh(action)
            dgm_logger.info(f"SafeActionQueue: Action {action.id} ({action_type}) enqueued.")
            return action.id

    def approve(self, action_id: int, operator: str = "manual"):
        with SessionLocal() as session:
            action = session.get(ActionRecord, action_id)
            if action:
                action.status = ActionStatus.APPROVED
                action.is_approved = True
                action.approved_by = operator
                action.approved_at = datetime.now()

                audit = json.loads(action.audit_trail)
                audit.append({
                    "timestamp": datetime.now().isoformat(),
                    "status": ActionStatus.APPROVED,
                    "operator": operator
                })
                action.audit_trail = json.dumps(audit)

                session.commit()
                dgm_logger.info(f"SafeActionQueue: Action {action_id} approved by {operator}.")

    def reject(self, action_id: int, reason: str, operator: str = "manual"):
        with SessionLocal() as session:
            action = session.get(ActionRecord, action_id)
            if action:
                action.status = ActionStatus.REJECTED
                action.error_message = reason

                audit = json.loads(action.audit_trail)
                audit.append({
                    "timestamp": datetime.now().isoformat(),
                    "status": ActionStatus.REJECTED,
                    "operator": operator,
                    "reason": reason
                })
                action.audit_trail = json.dumps(audit)

                session.commit()
                dgm_logger.info(f"SafeActionQueue: Action {action_id} rejected.")

    def get_action(self, action_id: int) -> Optional[Dict[str, Any]]:
        with SessionLocal() as session:
            action = session.get(ActionRecord, action_id)
            if action:
                return self._to_dict(action)
            return None

    def list_queued(self) -> List[Dict[str, Any]]:
        with SessionLocal() as session:
            actions = session.query(ActionRecord).filter(
                ActionRecord.status == ActionStatus.QUEUED
            ).all()
            return [self._to_dict(a) for a in actions]

    def _to_dict(self, action: ActionRecord) -> Dict[str, Any]:
        return {
            "id": action.id,
            "action_type": action.action_type,
            "payload": json.loads(action.payload),
            "status": action.status,
            "is_approved": action.is_approved,
            "approved_by": action.approved_by,
            "approved_at": action.approved_at.isoformat() if action.approved_at else None,
            "created_at": action.created_at.isoformat(),
            "audit_trail": json.loads(action.audit_trail),
            "error_message": action.error_message
        }
