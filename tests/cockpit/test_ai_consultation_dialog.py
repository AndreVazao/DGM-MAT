from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from cockpit.workspace.ai_consultation_dialog import AIConsultationDialog


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_consultation_requires_preview_provider_and_free_capacity(app):
    dialog = AIConsultationDialog(
        "http://127.0.0.1:8181/runtime",
        "thread-test-123",
    )
    dialog.goal.setPlainText("Review the current mission failure.")
    assert dialog.send_button.isEnabled() is False

    dialog._status_loaded = True
    dialog._consult_enabled = True
    dialog._preview_sha256 = "a" * 64
    dialog._refresh_controls()
    assert dialog.send_button.isEnabled() is False

    dialog.free_capacity.setChecked(True)
    dialog._refresh_controls()
    assert dialog.send_button.isEnabled() is True

    dialog.provider_checks["chatgpt"].setChecked(False)
    dialog._refresh_controls()
    assert dialog.send_button.isEnabled() is False
    dialog.close()


def test_consultation_payload_is_bound_to_active_thread_and_selected_providers(app):
    dialog = AIConsultationDialog(
        "http://127.0.0.1:8181/runtime",
        "thread-abc",
    )
    dialog.goal.setPlainText("Diagnose this test failure.")
    dialog.context.setPlainText("Branch: feature/test")
    dialog.provider_checks["chatgpt"].setChecked(False)
    dialog.provider_checks["gemini"].setChecked(True)
    dialog.provider_checks["qwen"].setChecked(True)
    dialog.free_capacity.setChecked(True)
    dialog._status_loaded = True
    dialog._consult_enabled = True
    dialog._preview_sha256 = "b" * 64

    captured = {}
    dialog._start_request = lambda action, method, path, payload=None: captured.update(
        action=action, method=method, path=path, payload=payload
    )
    dialog._enqueue()

    assert captured["action"] == "enqueue"
    assert captured["method"] == "POST"
    assert captured["path"] == "/recovery/browser-consult/enqueue"
    assert captured["payload"]["task_ref"] == "mobile-thread:thread-abc"
    assert captured["payload"]["providers"] == ["gemini", "qwen"]
    assert captured["payload"]["preview_sha256"] == "b" * 64
    assert captured["payload"]["free_capacity_confirmed"] is True
    dialog.close()


def test_status_response_limits_provider_choices_to_local_allowlist(app):
    dialog = AIConsultationDialog(
        "http://127.0.0.1:8181/runtime",
        "thread-status",
    )
    dialog._on_request_completed(
        "status",
        {"enabled": True, "free_providers_allowlisted": ["gemini", "qwen"]},
        "",
    )
    assert dialog.provider_checks["chatgpt"].isEnabled() is False
    assert dialog.provider_checks["gemini"].isEnabled() is True
    assert dialog.provider_checks["qwen"].isEnabled() is True
    assert dialog.provider_checks["grok"].isEnabled() is False
    assert dialog.send_button.isEnabled() is False
    dialog.close()


def test_consultation_approvals_are_started_sequentially(app):
    dialog = AIConsultationDialog(
        "http://127.0.0.1:8181/runtime",
        "thread-approval",
    )
    captured = []
    dialog._start_request = lambda action, method, path, payload=None: captured.append(
        (action, method, path)
    )
    dialog._on_request_completed(
        "enqueue",
        {"consultation_ids": ["consultation-a", "consultation-b"]},
        "",
    )
    assert captured == []
    dialog._on_worker_finished()
    assert captured == [(
        "approve", "POST", "/recovery/browser-consult/approve/consultation-a"
    )]
    dialog._on_request_completed("approve", {"status": "PENDING"}, "")
    dialog._on_worker_finished()
    assert captured[-1] == (
        "approve", "POST", "/recovery/browser-consult/approve/consultation-b"
    )
    dialog.close()
