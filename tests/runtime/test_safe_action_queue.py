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
