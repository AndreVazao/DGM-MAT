# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\provider_sync\\test_durable_provider_approval_store.py
import json
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.provider_sync import durable_provider_approval_store as store_module
from core.provider_sync.durable_provider_approval_store import DurableProviderApprovalStore
from core.runtime.safe_action_queue import ActionStatus
from core.storage.models import ActionRecord


class DatabaseApprovalQueue:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_approval(self, task_id):
        with self.session_factory() as session:
            actions = session.query(ActionRecord).filter(
                ActionRecord.action_type == "APPROVAL_REQUEST"
            ).all()
            for action in actions:
                payload = json.loads(action.payload)
                if payload.get("task_id") == task_id:
                    return {
                        "id": action.id,
                        "action_type": action.action_type,
                        "status": action.status,
                        "is_approved": action.is_approved,
                        "approved_by": action.approved_by,
                        "approved_at": action.approved_at.isoformat() if action.approved_at else None,
                        "payload": payload,
                    }
        return None
def make_store(tmp_path, monkeypatch, fingerprint):
    database_path = tmp_path / "approval-test.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    ActionRecord.__table__.create(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as session:
        session.add(ActionRecord(
            action_type="APPROVAL_REQUEST",
            payload=json.dumps({
                "task_id": "provider-task-1",
                "provider_request_fingerprint": fingerprint,
            }),
            status=ActionStatus.APPROVED,
            is_approved=False,
            approved_by="human-operator",
            approved_at=datetime.now(),
            audit_trail="[]",
        ))
        session.commit()
    monkeypatch.setattr(store_module, "SessionLocal", session_factory)
    queue = DatabaseApprovalQueue(session_factory)
    return DurableProviderApprovalStore(queue), session_factory, engine


def test_durable_approval_claim_is_single_use_in_sqlite(tmp_path, monkeypatch):
    store, sessions, engine = make_store(tmp_path, monkeypatch, "fingerprint-A")
    assert store.claim_approval("provider-task-1", "fingerprint-A") is True
    assert store.claim_approval("provider-task-1", "fingerprint-A") is False
    with sessions() as session:
        action = session.query(ActionRecord).first()
        assert action.status == ActionStatus.RUNNING
        assert action.is_approved is False
        assert len(json.loads(action.audit_trail)) == 1
    engine.dispose()


def test_durable_approval_rejects_fingerprint_mismatch_without_consuming(tmp_path, monkeypatch):
    store, sessions, engine = make_store(tmp_path, monkeypatch, "fingerprint-A")
    assert store.claim_approval("provider-task-1", "fingerprint-B") is False
    with sessions() as session:
        action = session.query(ActionRecord).first()
        assert action.status == ActionStatus.APPROVED
    engine.dispose()
