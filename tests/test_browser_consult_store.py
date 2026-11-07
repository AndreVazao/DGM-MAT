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
    assert queued["provider_count"] == 2
    assert store.claim_next("chatgpt") is None
    assert store.approve(queued["consultation_ids"][0], operator="test-operator") is True
    chat = store.claim_next("chatgpt")
    assert chat is not None
    assert chat["status"] == "RUNNING"
    assert "FREE-TIER" in chat["prompt"]
    completed = store.finish(
        chat["consultation_id"],
        claim_token=chat["claim_token"],
        response_text="The architecture is sound. Verify it with an end-to-end fixture.",
    )
    assert completed["status"] == "COMPLETED"
    assert completed["accepted"] is None
    assert completed["result_trusted"] is False
    assert store.claim_next("chatgpt") is None
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
