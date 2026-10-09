"""Tests for durable specialist handoffs and validated learning."""
import json

import pytest

from core.organization.specialist_collaboration import (
    CollaborationSecurityError,
    CollaborationStatus,
    SpecialistCollaborationStore,
)


def create_store(tmp_path):
    return SpecialistCollaborationStore(tmp_path / "collaborations")


def create_packet(store):
    return store.create_packet(
        goal="Diagnose and fix the failing provider test",
        project="DGM-MAT",
        department="engineering",
        specialist_role="Python test specialist",
        collaborator="Claude Code Free",
        context="Repository main is clean. Do not use paid APIs.",
        known_facts=["Full suite failed at provider adapter boundary."],
        attempted_steps=["Run focused provider tests."],
        evidence=["Failure reproduced locally."],
        constraints=["FREE-ONLY", "No remote exposure", "Do not touch FULL-MIRROR"],
        acceptance_criteria=["Focused tests pass", "No paid route can execute", "Document reusable lesson"],
    )


def test_packet_persists_and_exports_bounded_free_only_handoff(tmp_path):
    store = create_store(tmp_path)
    packet = create_packet(store)
    packet_id = packet["collaboration_id"]

    assert packet["policy"]["mode"] == "FREE_ONLY"
    assert packet["policy"]["paid_fallback"] is False
    assert "Do not use paid APIs" in packet["context"]
    loaded = create_store(tmp_path).get(packet_id)
    assert loaded.status == CollaborationStatus.PREPARED
    assert loaded.collaborator == "Claude Code Free"
    assert loaded.acceptance_criteria[0] == "Focused tests pass"


def test_free_limit_waits_without_paid_fallback(tmp_path):
    store = create_store(tmp_path)
    packet = create_packet(store)
    paused = store.mark_waiting_for_free_capacity(
        packet["collaboration_id"], reason="Free quota exhausted; resume after verified reset."
    )
    assert paused.status == CollaborationStatus.WAITING_FOR_FREE_CAPACITY
    assert paused.blocked_reason.startswith("Free quota exhausted")
    assert paused.result is None


def test_received_result_is_not_learning_until_independent_validation(tmp_path):
    store = create_store(tmp_path)
    packet = create_packet(store)
    received = store.record_result(
        packet["collaboration_id"],
        result="The failing assertion was caused by a test fake that did not implement quota reservation.",
        provenance="Claude Code Free browser session; user-authorized; no paid route used.",
    )
    assert received.status == CollaborationStatus.RESULT_RECEIVED
    assert received.reusable_lesson is None

    with pytest.raises(ValueError, match="tests_passed"):
        store.validate_result(
            packet["collaboration_id"],
            reviewer="agent:qa",
            review_notes="Review attempted but tests not run.",
            evidence=["Code inspection only."],
            tests_passed=False,
            reusable_lesson="Do not reuse yet.",
        )

    validated = store.validate_result(
        packet["collaboration_id"],
        reviewer="agent:qa",
        review_notes="Reviewed diff and verified focused tests.",
        evidence=["pytest focused suite: passed", "git diff --check: passed"],
        tests_passed=True,
        reusable_lesson="When provider execution requires quota reservation, test doubles must implement the same reservation contract.",
    )
    assert validated.status == CollaborationStatus.VALIDATED
    assert validated.reusable_lesson.startswith("When provider execution")
    assert "agent:qa" in validated.review_notes


def test_same_external_collaborator_cannot_self_validate(tmp_path):
    store = create_store(tmp_path)
    packet = create_packet(store)
    store.record_result(
        packet["collaboration_id"], result="change", provenance="Claude Code Free"
    )
    with pytest.raises(ValueError, match="Independent reviewer"):
        store.validate_result(
            packet["collaboration_id"],
            reviewer="Claude Code Free",
            review_notes="Looks good.",
            evidence=["I say so."],
            tests_passed=True,
            reusable_lesson="Lesson",
        )


def test_secrets_are_rejected_before_persistence(tmp_path):
    store = create_store(tmp_path)
    with pytest.raises(CollaborationSecurityError):
        store.create_packet(
            goal="Review configuration",
            project="DGM-MAT",
            department="security",
            specialist_role="security reviewer",
            collaborator="ChatGPT",
            context="api_key=sk-abcdefghijklmnopqrstuv",
        )
    assert store.list_packets() == []


def test_result_secret_is_rejected(tmp_path):
    store = create_store(tmp_path)
    packet = create_packet(store)
    with pytest.raises(CollaborationSecurityError):
        store.record_result(
            packet["collaboration_id"],
            result="access_token=abcdef123456789",
            provenance="Claude Code Free",
        )
    assert store.get(packet["collaboration_id"]).status == CollaborationStatus.PREPARED


def test_terminal_result_cannot_be_overwritten(tmp_path):
    store = create_store(tmp_path)
    packet = create_packet(store)
    store.record_result(packet["collaboration_id"], result="safe result", provenance="local agent")
    store.reject_result(packet["collaboration_id"], reviewer="agent:qa", reason="No test evidence")
    with pytest.raises(ValueError, match="terminal"):
        store.record_result(packet["collaboration_id"], result="replacement", provenance="other")
