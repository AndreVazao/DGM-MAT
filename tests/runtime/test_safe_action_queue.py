import pytest
from core.runtime.safe_action_queue import SafeActionQueue, ActionStatus

def test_action_queue_lifecycle():
    queue = SafeActionQueue()
    action_id = queue.enqueue("test_action", {"key": "value"})

    action = queue.get_action(action_id)
    assert action["status"] == ActionStatus.QUEUED
    assert action["is_approved"] is False

    queue.approve(action_id, operator="test_user")
    action = queue.get_action(action_id)
    assert action["status"] == ActionStatus.APPROVED
    assert action["is_approved"] is True
    assert action["approved_by"] == "test_user"

def test_action_queue_rejection():
    queue = SafeActionQueue()
    action_id = queue.enqueue("test_action_2", {"key": "value"})

    queue.reject(action_id, reason="Security risk")
    action = queue.get_action(action_id)
    assert action["status"] == ActionStatus.REJECTED
    assert action["error_message"] == "Security risk"


def test_action_decision_cannot_be_applied_twice():
    queue = SafeActionQueue()
    action_id = queue.enqueue("idempotency_approve_test", {"case": "approve"})

    assert queue.approve(action_id, operator="first_operator") is True
    assert queue.approve(action_id, operator="second_operator") is False

    action = queue.get_action(action_id)
    assert action["status"] == ActionStatus.APPROVED
    assert action["approved_by"] == "first_operator"
    assert sum(
        entry.get("status") == ActionStatus.APPROVED
        for entry in action["audit_trail"]
    ) == 1


def test_approved_action_can_be_claimed_only_once_across_consumers():
    from core.storage.database import SessionLocal

    queue = SafeActionQueue()
    action_id = queue.enqueue("atomic_claim_test", {"case": "single_claim"})
    assert queue.approve(action_id, operator="claim_test_operator") is True

    with SessionLocal() as session:
        assert queue._claim_approved_action(session, action_id) is True

    claimed = queue.get_action(action_id)
    assert claimed["status"] == ActionStatus.RUNNING
    running_entries = [
        entry for entry in claimed["audit_trail"]
        if entry.get("status") == ActionStatus.RUNNING
    ]
    assert len(running_entries) == 1

    # Simulates a second consumer that selected the row before the first claim
    # committed. The conditional update must reject the stale candidate.
    with SessionLocal() as competing_session:
        assert queue._claim_approved_action(competing_session, action_id) is False

    after_competitor = queue.get_action(action_id)
    assert after_competitor["status"] == ActionStatus.RUNNING
    assert sum(
        entry.get("status") == ActionStatus.RUNNING
        for entry in after_competitor["audit_trail"]
    ) == 1


def test_rejection_cannot_overwrite_an_approval():
    queue = SafeActionQueue()
    action_id = queue.enqueue("idempotency_reject_test", {"case": "reject"})
    assert queue.approve(action_id, operator="operator") is True

    assert queue.reject(action_id, reason="late rejection", operator="other") is False
    action = queue.get_action(action_id)
    assert action["status"] == ActionStatus.APPROVED
    assert action["is_approved"] is True
    assert action["error_message"] is None


def test_terminal_action_cannot_be_reapproved():
    from core.storage.database import SessionLocal
    from core.storage.models import ActionRecord

    queue = SafeActionQueue()
    action_id = queue.enqueue("terminal_reapproval_test", {"case": "completed"})
    assert queue.approve(action_id, operator="operator") is True

    with SessionLocal() as session:
        action = session.get(ActionRecord, action_id)
        action.status = ActionStatus.COMPLETED
        session.commit()

    assert queue.approve(action_id, operator="late_operator") is False
    assert queue.reject(action_id, reason="late rejection", operator="late_operator") is False
    action = queue.get_action(action_id)
    assert action["status"] == ActionStatus.COMPLETED
