from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.recovery.browser_consult_store import BrowserConsultStore, build_prompt


def _configure(monkeypatch, *providers):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", ",".join(providers))


def test_prompt_is_minimal_and_redacts_secrets():
    prompt = build_prompt(
        goal="Review this design; api_key=sk-abcdefghijklmnopqrstuvwxyz123456",
        context="Only inspect the recovery flow. bearer abcdefghijklmnopqrstuvwxyz1234567890",
    )
    assert "Review this design" in prompt
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in prompt
    assert "abcdefghijklmnopqrstuvwxyz1234567890" not in prompt
    assert "[REDACTED_SECRET]" in prompt
    assert "Do not claim to have run code" in prompt


def test_disabled_store_never_queues(monkeypatch, tmp_path):
    monkeypatch.delenv("DGM_BROWSER_CONSULT_ENABLED", raising=False)
    _configure(monkeypatch, "chatgpt")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "0")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    result = store.enqueue(task_ref="mission-1", goal="Review the recovery pipeline")
    assert result["status"] == "DISABLED"
    assert result["consultation_ids"] == []


def test_enqueue_claim_complete_and_cooldown(monkeypatch, tmp_path):
    _configure(monkeypatch, "chatgpt", "gemini", "grok")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3", cooldown_seconds=300)
    queued = store.enqueue(
        task_ref="mission-1",
        goal="Review the DGM-MAT browser recovery architecture",
        context="The archive is local and provider answers are untrusted.",
        providers=["chatgpt", "gemini", "grok"],
    )
    assert queued["status"] == "PENDING_APPROVAL"
    assert queued["provider_count"] == 3
    assert store.claim_next("chatgpt") is None
    assert store.approve(queued["consultation_ids"][0], operator="test-operator") is True
    chat = store.claim_next("chatgpt")
    assert chat is not None
    assert chat["status"] == "RUNNING"
    assert "free-tier" in chat["prompt"].casefold()
    completed = store.finish(
        chat["consultation_id"],
        claim_token=chat["claim_token"],
        response_text="The architecture is sound. Verify it with an end-to-end fixture.",
    )
    assert completed["status"] == "COMPLETED"
    assert completed["accepted"] is None
    assert completed["result_trusted"] is False
    assert store.claim_next("chatgpt") is None
    assert store.approve(queued["consultation_ids"][1], operator="test-operator") is True
    assert store.claim_next("gemini") is not None


def test_duplicate_task_provider_prompt_is_idempotent(monkeypatch, tmp_path):
    _configure(monkeypatch, "chatgpt")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    first = store.enqueue(task_ref="mission-2", goal="Classify this project request", providers=["chatgpt"])
    second = store.enqueue(task_ref="mission-2", goal="Classify this project request", providers=["chatgpt"])
    assert first["consultation_ids"] == second["consultation_ids"]
    assert store.status()["counts"]["PENDING_APPROVAL"] == 1


def test_rate_limit_and_login_are_blocked_with_no_automatic_retry(monkeypatch, tmp_path):
    _configure(monkeypatch, "grok")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    queued = store.enqueue(task_ref="mission-3", goal="Check one technical assumption", providers=["grok"])
    assert store.claim_next("grok") is None
    store.approve(queued["consultation_ids"][0], operator="test-operator")
    item = store.claim_next("grok")
    blocked = store.block(item["consultation_id"], claim_token=item["claim_token"], reason="rate_limited")
    assert blocked["status"] == "BLOCKED_RATE_LIMIT"
    assert blocked["automatic_retry"] is False
    assert store.claim_next("grok") is None
    assert store.status()["counts"]["BLOCKED_RATE_LIMIT"] == 1


def test_response_with_secret_is_never_archived(monkeypatch, tmp_path):
    _configure(monkeypatch, "gemini")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    queued = store.enqueue(task_ref="mission-4", goal="Review the security boundary", providers=["gemini"])
    store.approve(queued["consultation_ids"][0], operator="test-operator")
    item = store.claim_next("gemini")
    result = store.finish(
        item["consultation_id"],
        claim_token=item["claim_token"],
        response_text="The API key is sk-abcdefghijklmnopqrstuvwxyz123456",
    )
    assert result["status"] == "BLOCKED_SECRET_CONTENT"
    assert result["accepted"] is None
    assert store.status()["counts"]["BLOCKED_SECRET_CONTENT"] == 1


def test_restart_marks_inflight_consultation_blocked_and_never_replays(monkeypatch, tmp_path):
    _configure(monkeypatch, "chatgpt")
    path = tmp_path / "consult.sqlite3"
    store = BrowserConsultStore(path)
    queued = store.enqueue(task_ref="mission-5", goal="Review the parser", providers=["chatgpt"])
    store.approve(queued["consultation_ids"][0], operator="test-operator")
    item = store.claim_next("chatgpt")
    reopened = BrowserConsultStore(path)
    assert reopened.status()["counts"]["BLOCKED_RESTART"] == 1
    assert reopened.claim_next("chatgpt") is None


def test_claim_token_is_required_and_single_use(monkeypatch, tmp_path):
    _configure(monkeypatch, "chatgpt")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    queued = store.enqueue(task_ref="mission-6", goal="Review token binding", providers=["chatgpt"])
    store.approve(queued["consultation_ids"][0], operator="test-operator")
    item = store.claim_next("chatgpt")
    with pytest.raises(ValueError):
        store.finish(item["consultation_id"], claim_token="wrong-token", response_text="Nope")
    result = store.finish(
        item["consultation_id"],
        claim_token=item["claim_token"],
        response_text="Verified.",
    )
    assert result["status"] == "COMPLETED"
    with pytest.raises(ValueError):
        store.finish(
            item["consultation_id"],
            claim_token=item["claim_token"],
            response_text="Replay.",
        )


def test_fresh_review_queue_is_durable_and_requires_supported_privacy_provider(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt,gemini,grok")
    store = BrowserConsultStore(tmp_path / "fresh-review.sqlite3")
    with pytest.raises(ValueError, match="only ChatGPT and Gemini"):
        store.enqueue(
            task_ref="egm-task:task-1",
            goal="Review this bounded design.",
            providers=["grok"],
            review_mode="fresh_review",
            review_id="review-1",
        )
    queued = store.enqueue(
        task_ref="egm-task:task-1",
        goal="Review this bounded design.",
        providers=["chatgpt"],
        review_mode="fresh_review",
        review_id="review-1",
    )
    assert queued["status"] == "PENDING_APPROVAL"
    item_id = queued["consultation_ids"][0]
    assert store.approve(item_id, operator="operator")
    claimed = store.claim_next("chatgpt")
    assert claimed["review_mode"] == "fresh_review"
    assert claimed["review_id"] == "review-1"
    evidence = {
        "provider": "chatgpt",
        "source_id": "new-chat-1",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "chatgpt_temporary_unpersonalized",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id",
    }
    completed = store.finish(
        item_id,
        claim_token=claimed["claim_token"],
        response_text="Independent-looking review; still untrusted.",
        evidence=evidence,
    )
    assert completed["status"] == "COMPLETED"
    assert completed["review_mode"] == "fresh_review"
    assert completed["review_id"] == "review-1"
    assert completed["evidence"] == evidence
    reopened = BrowserConsultStore(tmp_path / "fresh-review.sqlite3")
    assert reopened.status()["counts"]["COMPLETED"] == 1


def test_fresh_review_evidence_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "gemini")
    store = BrowserConsultStore(tmp_path / "fresh-evidence.sqlite3")
    queued = store.enqueue(
        task_ref="egm-task:task-2",
        goal="Review this bounded design.",
        providers=["gemini"],
        review_mode="fresh_review",
        review_id="review-2",
    )
    consultation_id = queued["consultation_ids"][0]
    assert store.approve(consultation_id, operator="operator")
    claimed = store.claim_next("gemini")
    with pytest.raises(ValueError, match="privacy mode was not verified"):
        store.finish(
            consultation_id,
            claim_token=claimed["claim_token"],
            response_text="A response.",
            evidence={"provider": "gemini", "privacy_mode_verified": False},
        )


def test_fresh_review_result_requires_evidence_and_can_be_resumed(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt")
    store = BrowserConsultStore(tmp_path / "fresh-resume.sqlite3")
    queued = store.enqueue(
        task_ref="egm-task:task-3",
        goal="Review this bounded design.",
        providers=["chatgpt"],
        review_mode="fresh_review",
        review_id="review-resume",
    )
    consultation_id = queued["consultation_ids"][0]
    assert store.approve(consultation_id, operator="operator")
    claimed = store.claim_next("chatgpt")
    with pytest.raises(ValueError, match="requires host-observed"):
        store.finish(
            consultation_id,
            claim_token=claimed["claim_token"],
            response_text="A response without evidence.",
        )
    evidence = {
        "provider": "chatgpt",
        "source_id": "fresh-conversation-3",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "chatgpt_temporary_unpersonalized",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id_and_stable_response",
    }
    store.finish(
        consultation_id,
        claim_token=claimed["claim_token"],
        response_text="A bounded independent review.",
        evidence=evidence,
    )
    resumed = store.get_review("review-resume")
    assert resumed["status"] == "COMPLETED"
    assert resumed["reviewer_count"] == 1
    assert resumed["consultations"][0]["response_text"] == "A bounded independent review."
    assert resumed["consultations"][0]["evidence"] == evidence
    assert resumed["independence_attested"] is False
