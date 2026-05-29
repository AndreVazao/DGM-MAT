import json
import threading
import time
import traceback
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Column
from core.storage.database import Base, engine, SessionLocal
from core.storage.init_db import init_database
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

        # Ensure table exists using centralized idempotent init
        init_database()

        self._handlers: Dict[str, Callable] = {}
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_heartbeat: Optional[datetime] = None

        self._initialized = True
        dgm_logger.info("SafeActionQueue: Initialized.")

    def register_handler(self, action_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register a handler for a specific action type."""
        self._handlers[action_type] = handler
        dgm_logger.info(f"SafeActionQueue: Handler registered for {action_type}")

    def start_consumer(self):
        """Start the background consumer worker."""
        if self._worker_thread and self._worker_thread.is_alive():
            dgm_logger.warning("SafeActionQueue: Consumer already running.")
            return

        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._consumer_worker, daemon=True, name="SafeActionQueueConsumer")
        self._worker_thread.start()
        dgm_logger.info("QUEUE_CONSUMER_STARTED")

    def stop_consumer(self):
        """Stop the background consumer worker."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
            dgm_logger.info("SafeActionQueue: Consumer stopped.")

    def _consumer_worker(self):
        dgm_logger.info("QUEUE_CONSUMER_START")
        while not self._stop_event.is_set():
            try:
                self._last_heartbeat = datetime.now()

                # Polling for approved actions
                action_to_process = None
                with SessionLocal() as session:
                    action_to_process = session.query(ActionRecord).filter(
                        ActionRecord.status == ActionStatus.APPROVED,
                        ActionRecord.is_approved == True
                    ).order_by(ActionRecord.created_at.asc()).first()

                    if action_to_process:
                        # Mark as RUNNING immediately to prevent double processing
                        action_id = action_to_process.id
                        action_type = action_to_process.action_type
                        payload = json.loads(action_to_process.payload)

                        dgm_logger.info(f"QUEUE_POPPED: Action {action_id} ({action_type})")

                        action_to_process.status = ActionStatus.RUNNING
                        audit = json.loads(action_to_process.audit_trail)
                        audit.append({
                            "timestamp": datetime.now().isoformat(),
                            "status": ActionStatus.RUNNING,
                            "message": "Action started execution"
                        })
                        action_to_process.audit_trail = json.dumps(audit)
                        session.commit()
                    else:
                        dgm_logger.debug("QUEUE_EMPTY")

                if action_to_process:
                    # Execute handler
                    dgm_logger.info(f"QUEUE_EXECUTING: Action {action_id}")
                    handler = self._handlers.get(action_type)

                    try:
                        if handler:
                            handler_result = handler(payload)

                            with SessionLocal() as session:
                                act = session.get(ActionRecord, action_id)
                                act.status = ActionStatus.COMPLETED
                                audit = json.loads(act.audit_trail)
                                audit_entry = {
                                    "timestamp": datetime.now().isoformat(),
                                    "status": ActionStatus.COMPLETED,
                                    "message": "Action completed successfully"
                                }
                                if handler_result is not None:
                                    audit_entry["result"] = handler_result
                                audit.append(audit_entry)
                                act.audit_trail = json.dumps(audit)
                                session.commit()
                            dgm_logger.info(f"QUEUE_FINISHED: Action {action_id}")
                        else:
                            raise ValueError(f"No handler registered for action type: {action_type}")

                    except Exception as e:
                        error_trace = traceback.format_exc()
                        dgm_logger.error(f"QUEUE_FAILED: Action {action_id} - {e}\n{error_trace}")
                        with SessionLocal() as session:
                            act = session.get(ActionRecord, action_id)
                            act.status = ActionStatus.FAILED
                            act.error_message = str(e)
                            audit = json.loads(act.audit_trail)
                            audit.append({
                                "timestamp": datetime.now().isoformat(),
                                "status": ActionStatus.FAILED,
                                "error": str(e)
                            })
                            act.audit_trail = json.dumps(audit)
                            session.commit()
                else:
                    # Wait before next poll
                    dgm_logger.debug("QUEUE_WAITING")
                    time.sleep(5)

            except Exception as e:
                dgm_logger.error(f"SafeActionQueue: Consumer loop error: {e}")
                time.sleep(10) # Longer sleep on loop error

    def get_health(self) -> Dict[str, Any]:
        """Expose worker health state."""
        return {
            "worker_alive": self._worker_thread.is_alive() if self._worker_thread else False,
            "thread_count": 1 if self._worker_thread and self._worker_thread.is_alive() else 0,
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
            "handlers": list(self._handlers.keys())
        }

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

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        with SessionLocal() as session:
            actions = session.query(ActionRecord).order_by(ActionRecord.created_at.desc()).limit(limit).all()
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
