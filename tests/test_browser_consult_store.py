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
    _configure(monkeypatch, "chatgpt,gemini")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "0")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    result = store.enqueue(task_ref="mission-1", goal="Review the recovery pipeline")
    assert result["status"] == "DISABLED"
    assert result["consultation_ids"] == []


def test_enqueue_claim_complete_and_cooldown(monkeypatch, tmp_path):
    _configure(monkeypatch, "chatgpt", "gemini", "grok", "claude")
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


def test_claude_is_a_supported_free_browser_consult_provider(monkeypatch, tmp_path):
    _configure(monkeypatch, "claude")
    store = BrowserConsultStore(tmp_path / "claude-consult.sqlite3")
    queued = store.enqueue(
        task_ref="mission-claude",
        goal="Review this bounded technical change",
        providers=["claude"],
    )
    assert queued["provider_count"] == 1
    assert store.approve(queued["consultation_ids"][0], operator="test-operator") is True
    claimed = store.claim_next("claude")
    assert claimed is not None
    assert claimed["provider"] == "claude"


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


def test_fresh_review_queue_requires_both_providers_and_completes_only_after_both(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt,gemini,grok")
    store = BrowserConsultStore(tmp_path / "fresh-review.sqlite3")
    with pytest.raises(ValueError, match="both ChatGPT and Gemini"):
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
        providers=["chatgpt", "gemini"],
        review_mode="fresh_review",
        review_id="review-1",
    )
    assert queued["status"] == "PENDING_APPROVAL"
    assert queued["provider_count"] == 2
    assert queued["expected_provider_count"] == 2
    assert queued["expected_providers"] == ["chatgpt", "gemini"]
    ids = dict(zip(["chatgpt", "gemini"], queued["consultation_ids"]))
    for consultation_id in ids.values():
        assert store.approve(consultation_id, operator="operator")

    chatgpt = store.claim_next("chatgpt")
    assert chatgpt["review_mode"] == "fresh_review"
    assert chatgpt["review_id"] == "review-1"
    chatgpt_evidence = {
        "provider": "chatgpt",
        "source_id": "new-chat-1",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "chatgpt_temporary_unpersonalized",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id",
    }
    store.finish(
        ids["chatgpt"],
        claim_token=chatgpt["claim_token"],
        response_text="ChatGPT review; untrusted.",
        evidence=chatgpt_evidence,
    )
    partial = store.get_review("review-1")
    assert partial["status"] == "PENDING"
    assert partial["provider_count"] == 2
    assert partial["expected_provider_count"] == 2
    assert len([x for x in partial["consultations"] if x["status"] == "COMPLETED"]) == 1

    gemini = store.claim_next("gemini")
    gemini_evidence = {
        "provider": "gemini",
        "source_id": "new-gemini-chat-1",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "gemini_temporary_chat",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id",
    }
    completed = store.finish(
        ids["gemini"],
        claim_token=gemini["claim_token"],
        response_text="Gemini review; untrusted.",
        evidence=gemini_evidence,
    )
    assert completed["status"] == "COMPLETED"
    assert completed["review_mode"] == "fresh_review"
    assert completed["review_id"] == "review-1"
    assert completed["independence_attested"] is False
    assert completed["evidence"] == gemini_evidence
    reopened = BrowserConsultStore(tmp_path / "fresh-review.sqlite3")
    assert reopened.status()["counts"]["COMPLETED"] == 2


def test_fresh_review_evidence_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "gemini")
    store = BrowserConsultStore(tmp_path / "fresh-evidence.sqlite3")
    queued = store.enqueue(
        task_ref="egm-task:task-2",
        goal="Review this bounded design.",
        providers=["chatgpt", "gemini"],
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
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt,gemini")
    store = BrowserConsultStore(tmp_path / "fresh-resume.sqlite3")
    queued = store.enqueue(
        task_ref="egm-task:task-3",
        goal="Review this bounded design.",
        providers=["chatgpt", "gemini"],
        review_mode="fresh_review",
        review_id="review-resume",
    )
    ids = dict(zip(["chatgpt", "gemini"], queued["consultation_ids"]))
    for consultation_id in ids.values():
        assert store.approve(consultation_id, operator="operator")
    chatgpt = store.claim_next("chatgpt")
    with pytest.raises(ValueError, match="requires host-observed"):
        store.finish(
            ids["chatgpt"],
            claim_token=chatgpt["claim_token"],
            response_text="A response without evidence.",
        )
    chatgpt_evidence = {
        "provider": "chatgpt",
        "source_id": "fresh-conversation-3",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "chatgpt_temporary_unpersonalized",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id_and_stable_response",
    }
    store.finish(
        ids["chatgpt"],
        claim_token=chatgpt["claim_token"],
        response_text="A bounded ChatGPT review.",
        evidence=chatgpt_evidence,
    )
    partial = store.get_review("review-resume")
    assert partial["status"] == "PENDING"
    gemini = store.claim_next("gemini")
    gemini_evidence = {
        "provider": "gemini",
        "source_id": "fresh-gemini-conversation-3",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "gemini_temporary_chat",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id_and_stable_response",
    }
    store.finish(
        ids["gemini"],
        claim_token=gemini["claim_token"],
        response_text="A bounded Gemini review.",
        evidence=gemini_evidence,
    )
    resumed = store.get_review("review-resume")
    assert resumed["status"] == "COMPLETED"
    assert resumed["provider_count"] == 2
    assert resumed["expected_provider_count"] == 2
    assert resumed["consultations"][0]["result_trusted"] is False
    assert resumed["independence_attested"] is False


def test_peek_does_not_claim_or_consume_approved_fresh_review(monkeypatch, tmp_path):
    _configure(monkeypatch, "chatgpt")
    store = BrowserConsultStore(tmp_path / "fresh-peek.sqlite3")
    queued = store.enqueue(
        task_ref="egm-task:peek",
        goal="Review the design.",
        providers=["chatgpt", "gemini"],
        review_mode="fresh_review",
        review_id="review-peek",
    )
    consultation_id = queued["consultation_ids"][0]
    assert store.approve(consultation_id, operator="operator")
    peeked = store.peek_next("chatgpt")
    assert peeked["consultation_id"] == consultation_id
    assert peeked["review_mode"] == "fresh_review"
    assert store.status()["counts"]["PENDING"] == 1
    claimed = store.claim_next("chatgpt")
    assert claimed["consultation_id"] == consultation_id
    assert claimed["status"] == "RUNNING"


def test_fresh_review_id_cannot_be_rebound_to_another_task_or_brief(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt,gemini")
    store = BrowserConsultStore(tmp_path / "fresh-binding.sqlite3")
    store.enqueue(
        task_ref="egm-task:binding-1",
        goal="Review original design.",
        providers=["chatgpt", "gemini"],
        review_mode="fresh_review",
        review_id="review-bound",
    )
    with pytest.raises(ValueError, match="already bound"):
        store.enqueue(
            task_ref="egm-task:binding-2",
            goal="Review original design.",
            providers=["chatgpt", "gemini"],
            review_mode="fresh_review",
            review_id="review-bound",
        )
    with pytest.raises(ValueError, match="already bound"):
        store.enqueue(
            task_ref="egm-task:binding-1",
            goal="Review a different design.",
            providers=["chatgpt", "gemini"],
            review_mode="fresh_review",
            review_id="review-bound",
        )


def test_missing_expected_provider_keeps_fresh_review_pending(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "gemini")
    store = BrowserConsultStore(tmp_path / "fresh-missing-provider.sqlite3")
    queued = store.enqueue(
        task_ref="egm-task:missing-provider",
        goal="Review this bounded design.",
        providers=["chatgpt", "gemini"],
        review_mode="fresh_review",
        review_id="review-missing-provider",
    )
    assert queued["provider_count"] == 1
    assert queued["expected_provider_count"] == 2
    consultation_id = queued["consultation_ids"][0]
    assert store.approve(consultation_id, operator="operator")
    claimed = store.claim_next("gemini")
    evidence = {
        "provider": "gemini",
        "source_id": "fresh-gemini-missing-provider",
        "initial_source_id": None,
        "initial_visible_message_count": 0,
        "privacy_mode": "gemini_temporary_chat",
        "privacy_mode_verified": True,
        "verification": "blank_page_then_new_conversation_id",
    }
    store.finish(
        consultation_id,
        claim_token=claimed["claim_token"],
        response_text="Gemini only; still incomplete.",
        evidence=evidence,
    )
    review = store.get_review("review-missing-provider")
    assert review["status"] == "PENDING"
    assert review["missing_providers"] == ["chatgpt"]
    assert review["expected_provider_count"] == 2
