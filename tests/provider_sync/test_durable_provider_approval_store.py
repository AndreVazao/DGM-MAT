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


def test_provider_approval_request_persists_reviewable_envelope():
    class CaptureQueue:
        def __init__(self):
            self.action_type = None
            self.payload = None

        def enqueue(self, action_type, payload):
            self.action_type = action_type
            self.payload = payload
            return 44

    queue = CaptureQueue()
    store = DurableProviderApprovalStore(queue)
    messages = [{"role": "user", "content": "exact reviewed text"}]
    action_id = store.request_provider_approval(
        task_id="provider-task-envelope",
        provider_request_fingerprint="sha256-fingerprint",
        summary="Provider chat request",
        provider_id="provider-a",
        request_id="request-a",
        messages=messages,
    )
    assert action_id == 44
    assert queue.action_type == "APPROVAL_REQUEST"
    assert queue.payload["provider_request_fingerprint"] == "sha256-fingerprint"
    assert queue.payload["provider_id"] == "provider-a"
    assert queue.payload["request_id"] == "request-a"
    assert queue.payload["messages"] == messages


def test_provider_execution_outcome_is_audited_without_response_text(tmp_path, monkeypatch):
    store, sessions, engine = make_store(tmp_path, monkeypatch, "fingerprint-A")
    assert store.claim_approval("provider-task-1", "fingerprint-A") is True
    assert store.record_execution_outcome(
        "provider-task-1",
        success=True,
        code="completed",
        elapsed_ms=12.5,
    ) is True
    with sessions() as session:
        action = session.query(ActionRecord).first()
        assert action.status == ActionStatus.COMPLETED
        audit = json.loads(action.audit_trail)
        assert audit[-1]["event"] == "PROVIDER_EXECUTION_RESULT"
        assert audit[-1]["code"] == "completed"
        assert "response" not in audit[-1]
    engine.dispose()
