from __future__ import annotations

from datetime import timedelta

from core.providers.browser.browser_operator_queue import BrowserOperatorQueue


def make_queue(tmp_path, resolver=None):
    return BrowserOperatorQueue(
        tmp_path / "browser-operator.sqlite3",
        lease_seconds=30,
        mission_status_resolver=resolver or (lambda _mission_id: "RUNNING"),
    )


def enqueue(queue, *, approval_required=True, key="mission-1-chatgpt"):
    return queue.enqueue(
        idempotency_key=key,
        mission_id="mission_1234abcd",
        provider="chatgpt",
        source_id="conversation-123",
        conversation_url="https://chatgpt.com/c/conversation-123",
        message="Inspect the project and report evidence.",
        approval_required=approval_required,
    )


def test_tasks_require_approval_and_idempotency_prevents_duplicates(tmp_path):
    queue = make_queue(tmp_path)
    first = enqueue(queue)
    second = enqueue(queue)

    assert first["task_id"] == second["task_id"]
    assert first["status"] == "pending_approval"
    assert queue.claim_next(provider="chatgpt", worker_id="extension-session") is None
    assert queue.approve(first["task_id"], operator="local-operator") is True
    assert queue.get(first["task_id"])["approved_by"] == "local-operator"
    assert queue.approve(first["task_id"], operator="local-operator") is False

    claimed = queue.claim_next(provider="chatgpt", worker_id="extension-session")
    assert claimed is not None
    assert claimed["task_id"] == first["task_id"]
    assert claimed["status"] == "claimed"
    assert claimed["claim_token"]


def test_claim_is_single_use_and_result_requires_owner_token(tmp_path):
    queue = make_queue(tmp_path)
    task = enqueue(queue, approval_required=False)
    assert queue.get(task["task_id"])["approved_by"] == "mission-engine"
    claimed = queue.claim_next(provider="chatgpt", worker_id="extension-session")
    assert claimed is not None

    assert queue.complete(
        task["task_id"],
        worker_id="other-session",
        claim_token=claimed["claim_token"],
        result={"assistant_text": "No."},
    ) is False
    assert queue.complete(
        task["task_id"],
        worker_id="extension-session",
        claim_token="wrong-token",
        result={"assistant_text": "No."},
    ) is False
    assert queue.complete(
        task["task_id"],
        worker_id="extension-session",
        claim_token=claimed["claim_token"],
        result={"assistant_text": "Verified response", "provider": "chatgpt"},
    ) is True
    assert queue.complete(
        task["task_id"],
        worker_id="extension-session",
        claim_token=claimed["claim_token"],
        result={"assistant_text": "Duplicate"},
    ) is False
    saved = queue.get(task["task_id"])
    assert saved["status"] == "completed"
    assert saved["result"]["assistant_text"] == "Verified response"


def test_expired_claim_goes_to_review_and_is_never_replayed(tmp_path, monkeypatch):
    queue = make_queue(tmp_path)
    task = enqueue(queue, approval_required=False)
    claimed = queue.claim_next(provider="chatgpt", worker_id="extension-session")
    assert claimed is not None

    original_now = queue._now
    monkeypatch.setattr(queue, "_now", lambda: original_now() + timedelta(seconds=45))
    assert queue.claim_next(provider="chatgpt", worker_id="extension-session-2") is None

    saved = queue.get(task["task_id"])
    assert saved["status"] == "needs_review"
    assert "automatic replay prohibited" in saved["error"]
    assert queue.claim_next(provider="chatgpt", worker_id="extension-session-3") is None


def test_provider_isolation_and_failure_checkpoint(tmp_path):
    queue = make_queue(tmp_path)
    task = queue.enqueue(
        idempotency_key="mission-2-gemini",
        mission_id="mission_1234abcd",
        provider="gemini",
        source_id="gemini-1",
        conversation_url="https://gemini.google.com/app/gemini-1",
        message="Continue the analysis.",
        approval_required=False,
    )
    assert queue.claim_next(provider="chatgpt", worker_id="extension-session") is None
    claimed = queue.claim_next(provider="gemini", worker_id="extension-session")
    assert claimed is not None
    assert queue.fail(
        task["task_id"],
        worker_id="extension-session",
        claim_token=claimed["claim_token"],
        reason="provider rate limit",
        blocked=True,
    ) is True
    assert queue.get(task["task_id"])["status"] == "blocked"

def test_approval_bypass_requires_a_fresh_running_parent_mission(tmp_path):
    queue = make_queue(tmp_path, lambda _mission_id: "APPROVAL_PENDING")
    try:
        enqueue(queue, approval_required=False)
    except ValueError as exc:
        assert "RUNNING parent mission" in str(exc)
    else:
        raise AssertionError("approval bypass was accepted for a non-running mission")
    pending = enqueue(queue, approval_required=True, key="pending-approval-task")
    assert pending["status"] == "pending_approval"


def test_claim_rechecks_parent_mission_and_blocks_terminal_parent(tmp_path):
    state = {"status": "RUNNING"}
    queue = make_queue(tmp_path, lambda _mission_id: state["status"])
    task = enqueue(queue, approval_required=False)
    state["status"] = "COMPLETED"

    assert queue.claim_next(provider="chatgpt", worker_id="extension-session") is None
    saved = queue.get(task["task_id"])
    assert saved["status"] == "needs_review"
    assert "parent_mission_missing_or_terminal" in saved["error"]


def test_approved_task_waits_until_parent_mission_is_running(tmp_path):
    state = {"status": "APPROVAL_PENDING"}
    queue = make_queue(tmp_path, lambda _mission_id: state["status"])
    task = enqueue(queue, approval_required=True)
    assert queue.approve(task["task_id"], operator="local-operator") is True
    assert queue.claim_next(provider="chatgpt", worker_id="extension-session") is None
    assert queue.get(task["task_id"])["status"] == "queued"

    state["status"] = "RUNNING"
    claimed = queue.claim_next(provider="chatgpt", worker_id="extension-session")
    assert claimed is not None
    assert claimed["task_id"] == task["task_id"]


def test_terminal_parent_mission_cannot_receive_browser_task(tmp_path):
    queue = make_queue(tmp_path, lambda _mission_id: "CANCELLED")
    try:
        enqueue(queue, approval_required=True)
    except ValueError as exc:
        assert "terminal mission" in str(exc)
    else:
        raise AssertionError("terminal mission accepted a browser task")

def test_idempotency_key_cannot_change_approval_requirement(tmp_path):
    queue = make_queue(tmp_path)
    first = enqueue(queue, approval_required=False, key="stable-approval-key")
    try:
        enqueue(queue, approval_required=True, key="stable-approval-key")
    except ValueError as exc:
        assert "different task envelope" in str(exc)
    else:
        raise AssertionError("idempotency key changed approval requirement")
    assert queue.get(first["task_id"])["approval_required"] is False
