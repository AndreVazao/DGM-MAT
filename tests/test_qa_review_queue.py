"""Safety and durability tests for the specialist QA review work queue."""
from __future__ import annotations

import pytest

from core.organization.models import Message, MessagePriority
from core.organization.qa_intake_worker import QAIntakeWorker
from core.organization.qa_review_queue import QAReviewQueue


def _message(correlation_id: str = "corr-qa-001") -> Message:
    return Message(
        sender_id="agent:builder",
        recipient_id="agent:bug-hunter",
        subject="Review implementation result",
        body="Inspect the change and verify the tests.",
        mission_id="mission-test-01",
        priority=MessagePriority.HIGH,
        correlation_id=correlation_id,
    )


def test_enqueue_is_idempotent_and_rejects_conflicting_correlation(tmp_path):
    queue = QAReviewQueue(tmp_path / "qa.sqlite3")
    message = _message()
    first = QAIntakeWorker(queue)(message)
    second = QAIntakeWorker(queue)(message)
    assert first["status"] == "REVIEW_QUEUED"
    assert first["work_item"]["work_item_id"] == second["work_item"]["work_item_id"]
    assert len(queue.list_items()) == 1
    changed = _message()
    changed.body = "A conflicting body must not overwrite the first request."
    with pytest.raises(ValueError, match="Conflicting"):
        QAIntakeWorker(queue)(changed)


def test_queue_survives_reopen_and_intake_does_not_complete_review(tmp_path):
    path = tmp_path / "qa.sqlite3"
    queue = QAReviewQueue(path)
    result = QAIntakeWorker(queue)(_message())
    item_id = result["work_item"]["work_item_id"]
    assert result["independent_review_performed"] is False
    assert result["tests_executed"] is False
    queue.close()

    reopened = QAReviewQueue(path)
    item = reopened.get(item_id)
    assert item["status"] == "PENDING"
    assert item["attempts"] == 0
    assert item["mission_id"] == "mission-test-01"
    assert item["evidence"] == []
    assert item["tests_executed"] == []


def test_completion_requires_real_check_records_and_current_owner(tmp_path):
    queue = QAReviewQueue(tmp_path / "qa.sqlite3")
    item = queue.enqueue(correlation_id="corr-2", source_message_id="msg-2", mission_id="m-2",
                         subject="Review", request_body="Inspect", priority="NORMAL")
    claimed = queue.claim(item["work_item_id"], "agent:qa-reviewer")
    assert claimed["status"] == "IN_PROGRESS"
    assert claimed["attempts"] == 1
    with pytest.raises(ValueError, match="current owner"):
        queue.complete(item["work_item_id"], owner_id="agent:other", review_outcome="PASS",
                       tests_executed=[{"name": "pytest", "result": "passed"}],
                       evidence=[{"source": "local", "summary": "test output"}])
    with pytest.raises(ValueError, match="at least one"):
        queue.complete(item["work_item_id"], owner_id="agent:qa-reviewer", review_outcome="PASS",
                       tests_executed=[], evidence=[{"source": "local", "summary": "test output"}])
    completed = queue.complete(item["work_item_id"], owner_id="agent:qa-reviewer", review_outcome="PASS",
                               tests_executed=[{"name": "pytest", "result": "passed"}],
                               evidence=[{"source": "local-test-run", "summary": "pytest output captured"}])
    assert completed["status"] == "COMPLETED"
    assert completed["review_outcome"] == "PASS"
    with pytest.raises(ValueError, match="terminal"):
        queue.claim(item["work_item_id"], "agent:qa-reviewer")


def test_block_retry_and_attempt_limit_are_explicit(tmp_path):
    queue = QAReviewQueue(tmp_path / "qa.sqlite3")
    item = queue.enqueue(correlation_id="corr-3", source_message_id="msg-3", mission_id=None,
                         subject="Review", request_body="Inspect", priority="NORMAL", max_attempts=1)
    queue.claim(item["work_item_id"], "reviewer")
    blocked = queue.block(item["work_item_id"], reason="Required test tool unavailable", owner_id="reviewer")
    assert blocked["status"] == "BLOCKED"
    with pytest.raises(ValueError, match="Maximum review attempts"):
        queue.retry(item["work_item_id"], reason="Retry requested")
    with pytest.raises(ValueError, match="supervisor intervention"):
        queue.claim(item["work_item_id"], "reviewer")


def test_invalid_status_and_empty_evidence_are_rejected(tmp_path):
    queue = QAReviewQueue(tmp_path / "qa.sqlite3")
    with pytest.raises(ValueError, match="Unsupported status"):
        queue.list_items(status="DONE")
    item = queue.enqueue(correlation_id="corr-4", source_message_id="msg-4", mission_id=None,
                         subject="Review", request_body="Inspect", priority="LOW")
    queue.claim(item["work_item_id"], "reviewer")
    with pytest.raises(ValueError, match="evidence records"):
        queue.complete(item["work_item_id"], owner_id="reviewer", review_outcome="PASS",
                       tests_executed=[{"name": "unit", "result": "passed"}], evidence=[])
