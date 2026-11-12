# Path: C:\ProgramasGodMode\DGM-MAT\tests\cockpit\test_command_console_worker.py
import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from cockpit.widgets.command_console import CommandConsoleWidget, _RuntimeRequestWorker


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_runtime_http_request_runs_off_gui_thread(monkeypatch):
    gui_thread_id = threading.get_ident()
    request_thread_ids = []

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"status": "success", "mission_id": "mission-test-1"}

    def fake_post(*args, **kwargs):
        request_thread_ids.append(threading.get_ident())
        return FakeResponse()

    monkeypatch.setattr("cockpit.widgets.command_console.authenticated_request", fake_post)
    worker = _RuntimeRequestWorker(
        "http://127.0.0.1:8181/runtime",
        "test directive",
    )
    worker.start()
    assert worker.wait(3000), "HTTP worker did not finish within three seconds"
    assert request_thread_ids
    assert request_thread_ids[0] != gui_thread_id


def test_console_escapes_user_supplied_html(app):
    widget = CommandConsoleWidget()
    widget._append_message("User", "<script>alert(1)</script>", "user")
    rendered = widget.output.toHtml()
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;" in rendered
    widget.close()


def test_console_stays_disabled_when_runtime_is_offline(app):
    widget = CommandConsoleWidget()
    widget.set_enabled(False)
    assert not widget.input_field.isEnabled()
    assert not widget.send_btn.isEnabled()
    widget.close()


def test_archive_button_targets_selected_thread_and_toggles_restore(app, monkeypatch):
    widget = CommandConsoleWidget()
    from PySide6.QtWidgets import QListWidgetItem
    from PySide6.QtCore import Qt

    item = QListWidgetItem("Projeto [active]")
    item.setData(Qt.ItemDataRole.UserRole, "thread-archive-test")
    item.setData(Qt.ItemDataRole.UserRole + 1, "active")
    widget.thread_list.addItem(item)
    widget.thread_list.setCurrentItem(item)
    captured = []
    monkeypatch.setattr(
        widget,
        "_conversation_request",
        lambda action, method, path, **kwargs: captured.append((action, method, path)),
    )

    widget._archive_selected_thread()
    assert captured[-1] == (
        "thread-archive", "POST", "/mobile/threads/thread-archive-test/archive"
    )

    item.setData(Qt.ItemDataRole.UserRole + 1, "archived")
    widget._archive_selected_thread()
    assert captured[-1] == (
        "thread-restore", "POST", "/mobile/threads/thread-archive-test/restore"
    )
    widget.close()


def test_archived_active_conversation_disables_message_submission(app):
    widget = CommandConsoleWidget()
    widget._active_thread_id = "thread-archived"
    widget._active_thread_status = "archived"
    widget._refresh_controls()
    assert widget.input_field.isEnabled() is False
    assert widget.send_btn.isEnabled() is False
    assert "arquivada" in widget.input_field.placeholderText().casefold()
    widget.close()


def test_archive_restore_response_updates_state_without_unbound_data(app, monkeypatch):
    widget = CommandConsoleWidget()
    widget._active_thread_id = "thread-archive-test"
    widget._active_thread_status = "active"
    requests = []
    monkeypatch.setattr(
        widget,
        "_conversation_request",
        lambda action, method, path, **kwargs: requests.append((action, method, path)),
    )

    widget._on_conversation_request_completed(
        "thread-archive",
        {"id": "thread-archive-test", "status": "archived"},
        "",
    )

    assert widget._active_thread_status == "archived"
    assert requests == [("threads-list", "GET", "/mobile/threads")]
    assert "arquivada" in widget.input_field.placeholderText().casefold()
    widget.close()



def test_live_refresh_appends_only_new_messages_and_keeps_provider_provenance(app):
    widget = CommandConsoleWidget()
    widget.history.clear()  # Exclude the widget startup greeting from transcript assertions.
    widget._active_thread_id = "thread-live"
    first = {
        "id": "msg-provider-1",
        "role": "assistant",
        "content": "Proposta do ChatGPT",
        "metadata": {
            "source": "dgm-browser-consultation",
            "provider": "chatgpt",
            "result_trusted": False,
        },
    }
    widget._append_persisted_message(first)
    widget._append_persisted_message(first)

    assert len(widget.history) == 1
    assert widget.history[0]["sender"] == "CHATGPT — resposta externa não verificada"
    assert "Proposta do ChatGPT" in widget.history[0]["text"]
    widget.close()


def test_live_refresh_ignores_response_for_a_different_active_thread(app):
    widget = CommandConsoleWidget()
    widget._active_thread_id = "thread-current"
    widget._thread_refresh_inflight = True
    widget._on_conversation_request_completed(
        "thread-refresh",
        {
            "id": "thread-previous",
            "messages": [{
                "id": "msg-stale",
                "role": "assistant",
                "content": "Não deve aparecer",
                "metadata": {},
            }],
        },
        "",
    )

    assert widget._thread_refresh_inflight is False
    assert all(item["text"] != "Não deve aparecer" for item in widget.history)
    widget.close()


def test_live_refresh_requests_only_the_visible_active_thread(app, monkeypatch):
    widget = CommandConsoleWidget()
    widget._active_thread_id = "thread-live"
    widget._thread_refresh_inflight = False
    monkeypatch.setattr(widget, "isVisible", lambda: True)
    monkeypatch.setattr(widget, "_conversation_workers_busy", lambda: False)
    captured = []
    monkeypatch.setattr(
        widget,
        "_conversation_request",
        lambda action, method, path, **kwargs: captured.append((action, method, path)),
    )

    widget._refresh_active_thread()

    assert captured == [(
        "thread-refresh", "GET", "/mobile/threads/thread-live"
    )]
    assert widget._thread_refresh_inflight is True
    widget.close()



def test_transcript_write_response_marks_local_echo_as_seen(app):
    widget = CommandConsoleWidget()
    widget._active_thread_id = "thread-live"
    widget._on_conversation_request_completed(
        "send-user-entry",
        {
            "thread_id": "thread-live",
            "message": {"id": "msg-local-user", "role": "user", "content": "Olá"},
        },
        "",
    )

    assert "msg-local-user" in widget._seen_message_ids
    widget.close()



def test_inline_consultation_panel_queues_selected_provider_for_active_thread(app, monkeypatch):
    from cockpit.workspace.ai_consultation_inline_panel import AIConsultationInlinePanel

    panel = AIConsultationInlinePanel("http://127.0.0.1:8181/runtime")
    panel.set_thread_context("thread-inline", "Revê esta proposta técnica.", "Tu: contexto anterior\nDGM-MAT: resposta anterior")
    panel._status_loaded = True
    panel._consult_enabled = True
    panel._allowed_providers = {"claude"}
    panel._refresh_controls()
    panel.provider_checks["claude"].setChecked(True)
    captured = []
    monkeypatch.setattr(
        panel,
        "_start_request",
        lambda action, method, path, payload=None: captured.append((action, method, path, payload)),
    )

    panel._enqueue()

    assert captured[0][0:3] == (
        "enqueue", "POST", "/recovery/browser-consult/enqueue"
    )
    assert captured[0][3]["task_ref"] == "mobile-thread:thread-inline"
    assert captured[0][3]["providers"] == ["claude"]
    assert "contexto anterior" in captured[0][3]["context"]
    assert captured[0][3]["free_capacity_confirmed"] is True
    panel.close()


def test_inline_consultation_completion_is_bound_to_originating_thread(app):
    from cockpit.workspace.ai_consultation_inline_panel import AIConsultationInlinePanel

    panel = AIConsultationInlinePanel("http://127.0.0.1:8181/runtime")
    panel._pending_thread_id = "thread-origin"
    captured = []
    panel.status_message.connect(lambda thread_id, message: captured.append((thread_id, message)))

    panel._approve_next()

    assert captured and captured[0][0] == "thread-origin"
    assert "Ainda não foi enviada" in captured[0][1]
    panel.close()



def test_explicit_provider_command_dispatches_to_provider_worker_not_mission(app, monkeypatch):
    widget = CommandConsoleWidget()
    widget._active_thread_id = "thread-provider-intent"
    widget._pending_directive = "Pede ajuda ao ChatGPT e Grok: avalia esta arquitetura."
    captured = []
    monkeypatch.setattr(
        widget,
        "_start_provider_consultation",
        lambda thread_id, goal, providers, context: captured.append(
            (thread_id, goal, providers, context)
        ),
    )
    monkeypatch.setattr(
        widget,
        "_start_request",
        lambda *args, **kwargs: pytest.fail("Explicit provider request must not create a mission"),
    )
    monkeypatch.setattr(widget, "_flush_transcript_queue", lambda: None)

    widget._on_conversation_request_completed("send-user-entry", {}, "")

    assert captured
    assert captured[0][0] == "thread-provider-intent"
    assert captured[0][1] == "avalia esta arquitetura."
    assert captured[0][2] == ("chatgpt", "grok")
    widget.close()


def test_provider_worker_previews_enqueues_and_approves_only_allowlisted_providers(app, monkeypatch):
    from cockpit.workspace.provider_consultation_worker import ProviderConsultationWorker

    calls = []

    class FakeResponse:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def fake_request(method, url, json=None, timeout=None):
        calls.append((method, url, json))
        if url.endswith("/recovery/browser-consult/status") and len(calls) == 1:
            return FakeResponse({
                "enabled": True,
                "free_providers_allowlisted": ["chatgpt", "grok"],
            })
        if url.endswith("/recovery/browser-consult/preview"):
            return FakeResponse({"prompt_sha256": "a" * 64, "prompt_redacted": False})
        if url.endswith("/recovery/browser-consult/enqueue"):
            return FakeResponse({
                "status": "PENDING_APPROVAL",
                "consultation_ids": ["consult-chatgpt", "consult-grok"],
            })
        if url.endswith("/recovery/browser-consult/status"):
            return FakeResponse({"recent": [
                {"consultation_id": "consult-chatgpt", "status": "PENDING_APPROVAL"},
                {"consultation_id": "consult-grok", "status": "PENDING_APPROVAL"},
            ]})
        if url.endswith("/approve/consult-chatgpt") or url.endswith("/approve/consult-grok"):
            return FakeResponse({"status": "PENDING"})
        raise AssertionError("Unexpected provider consultation request: " + url)

    monkeypatch.setattr(
        "cockpit.workspace.provider_consultation_worker.authenticated_request",
        fake_request,
    )
    worker = ProviderConsultationWorker(
        "http://127.0.0.1:8181/runtime",
        "thread-provider",
        "Avalia a arquitetura",
        "Contexto recente redigido no backend.",
        ("chatgpt", "grok"),
    )
    emitted = []
    worker.completed.connect(lambda sender, message, kind: emitted.append((sender, message, kind)))
    worker.run()

    assert [call[0] for call in calls] == ["GET", "POST", "POST", "GET", "POST", "POST"]
    assert calls[2][2]["task_ref"] == "mobile-thread:thread-provider"
    assert calls[2][2]["providers"] == ["chatgpt", "grok"]
    assert emitted and emitted[0][0] == "Sistema"
    assert "Ainda não afirmo que foram enviadas" in emitted[0][1]


def test_provider_worker_fails_closed_when_provider_is_not_free_allowlisted(app, monkeypatch):
    from cockpit.workspace.provider_consultation_worker import ProviderConsultationWorker

    calls = []

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"enabled": True, "free_providers_allowlisted": ["chatgpt"]}

    monkeypatch.setattr(
        "cockpit.workspace.provider_consultation_worker.authenticated_request",
        lambda method, url, **kwargs: (calls.append((method, url)) or FakeResponse()),
    )
    worker = ProviderConsultationWorker(
        "http://127.0.0.1:8181/runtime",
        "thread-provider",
        "Avalia a arquitetura",
        "",
        ("chatgpt", "claude"),
    )
    emitted = []
    worker.completed.connect(lambda sender, message, kind: emitted.append((sender, message, kind)))
    worker.run()

    assert len(calls) == 1
    assert "Claude não está configurado" in emitted[0][1]
    assert "fallback pago" in emitted[0][1]
    assert emitted[0][2] == "error"



def test_provider_worker_reports_partial_approval_without_retry(app, monkeypatch):
    from cockpit.workspace.provider_consultation_worker import ProviderConsultationWorker

    calls = []

    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self.payload = payload or {}

        def json(self):
            return self.payload

    def fake_request(method, url, json=None, timeout=None):
        calls.append((method, url))
        if url.endswith("/recovery/browser-consult/status") and len(calls) == 1:
            return FakeResponse(200, {
                "enabled": True,
                "free_providers_allowlisted": ["chatgpt", "grok"],
            })
        if url.endswith("/recovery/browser-consult/preview"):
            return FakeResponse(200, {"prompt_sha256": "b" * 64})
        if url.endswith("/recovery/browser-consult/enqueue"):
            return FakeResponse(200, {"consultation_ids": ["consult-1", "consult-2"]})
        if url.endswith("/recovery/browser-consult/status"):
            return FakeResponse(200, {"recent": []})
        if url.endswith("/approve/consult-1"):
            return FakeResponse(200, {"status": "PENDING"})
        if url.endswith("/approve/consult-2"):
            return FakeResponse(503)
        raise AssertionError("Unexpected request")

    monkeypatch.setattr(
        "cockpit.workspace.provider_consultation_worker.authenticated_request",
        fake_request,
    )
    worker = ProviderConsultationWorker(
        "http://127.0.0.1:8181/runtime",
        "thread-provider",
        "Revê isto",
        "",
        ("chatgpt", "grok"),
    )
    emitted = []
    worker.completed.connect(lambda sender, message, kind: emitted.append((sender, message, kind)))
    worker.run()

    assert len([call for call in calls if "/approve/" in call[1]]) == 2
    assert "1 consulta(s) já ficaram aprovadas" in emitted[0][1]
    assert "Verifica o estado da fila antes de repetir" in emitted[0][1]
