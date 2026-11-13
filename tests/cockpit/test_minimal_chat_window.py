import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import requests
from PySide6.QtWidgets import QApplication

from cockpit.minimal_chat_window import MinimalChatWindow
from cockpit.widgets.command_console import (
    CommandConsoleWidget,
    _ConversationRequestWorker,
    _RuntimeRequestWorker,
)


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_default_cockpit_is_chat_first_with_sidebar_history(qt_app):
    window = MinimalChatWindow()

    assert window.windowTitle() == "DGM-MAT — Assistente"
    assert window.chat.input_field is not None
    assert window.chat.send_btn is not None
    assert window.chat.thread_list.parent() is not None
    assert window.chat.search_field.placeholderText() == "Pesquisar conversas…"
    assert window.chat.new_thread_btn.text().strip().endswith("Nova conversa")
    assert window.chat.search_more_btn.text() == "Mais conversas"
    assert window.chat.archive_thread_btn.text() == "Arquivar / restaurar"

    window.close()


def test_chat_escapes_user_and_runtime_html(qt_app):
    chat = CommandConsoleWidget()
    chat._append_message("user<script>", "<img src=x onerror=alert(1)>", "user")

    rendered = chat.output.toHtml()
    assert "&lt;script&gt;" in rendered
    assert "&lt;img" in rendered
    assert "<img src=x onerror=alert(1)>" not in rendered

    chat.close()


def test_runtime_worker_retries_status_timeouts_without_duplicate_submission(
    qt_app, monkeypatch
):
    class Response:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self.payload = payload

        def json(self):
            return self.payload

    calls = []
    sleeps = []
    get_count = 0

    def fake_request(method, suffix, **kwargs):
        nonlocal get_count
        calls.append((method, suffix, kwargs))
        if method == "POST":
            return Response(201, {
                "status": "success",
                "mission_id": "mission_b55c3887",
                "mission_status": "QUEUED",
            })

        get_count += 1
        if get_count <= 2:
            raise requests.Timeout("temporary checkpoint read timeout")
        return Response(200, {
            "mission_id": "mission_b55c3887",
            "status": "FAILED",
            "action_status": "FAILED",
            "error": "Repository scan failed safely",
        })

    worker = _RuntimeRequestWorker(
        "http://127.0.0.1:8181/runtime",
        "faz uma pesquisa nas repos Barbuidos e reporta os seus estados",
    )
    monkeypatch.setattr(worker, "_request", fake_request)
    worker._sleep = lambda seconds: sleeps.append(seconds)
    emitted = []
    worker.completed.connect(lambda *args: emitted.append(args))

    worker.run()

    assert sum(method == "POST" and suffix == "/missions" for method, suffix, _ in calls) == 1
    assert sum(method == "GET" and suffix == "/missions/mission_b55c3887" for method, suffix, _ in calls) == 3
    assert sleeps == [2.0, 2.0]
    messages = [message for _sender, message, _kind in emitted]
    assert any("Missão falhou (mission_b55c3887)" in message for message in messages)
    assert any("Repository scan failed safely" in message for message in messages)
    assert not any("continua sem estado final" in message for message in messages)



def test_desktop_chat_exposes_thread_history_controls(qt_app):
    chat = CommandConsoleWidget()

    assert chat.new_thread_btn.text() == "＋ Nova conversa"
    assert chat.search_btn.text() == "Pesquisar"
    assert chat.search_more_btn.text() == "Mais resultados"
    assert not chat.search_more_btn.isEnabled()
    assert chat.thread_list is not None
    assert chat._active_thread_id is None

    chat.close()


def test_conversation_worker_uses_authenticated_api_off_gui_thread(qt_app, monkeypatch):
    import threading

    gui_thread = threading.get_ident()
    request_threads = []
    calls = []

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"threads": []}

    def fake_request(method, url, **kwargs):
        request_threads.append(threading.get_ident())
        calls.append((method, url, kwargs))
        return Response()

    monkeypatch.setattr(
        "cockpit.widgets.command_console.authenticated_request", fake_request
    )
    worker = _ConversationRequestWorker(
        "http://127.0.0.1:8181/runtime",
        "threads-list",
        "GET",
        "/mobile/threads",
    )
    emitted = []
    worker.completed.connect(lambda *args: emitted.append(args))
    worker.start()

    assert worker.wait(3000)
    qt_app.processEvents()
    assert request_threads and request_threads[0] != gui_thread
    assert calls[0][0:2] == ("GET", "http://127.0.0.1:8181/mobile/threads")
    assert emitted == [("threads-list", {"threads": []}, "")]


def test_mission_is_not_submitted_until_user_entry_is_persisted(qt_app, monkeypatch):
    chat = CommandConsoleWidget()
    chat._active_thread_id = "thread-existing"
    requests = []
    submitted = []

    monkeypatch.setattr(
        chat,
        "_conversation_request",
        lambda *args, **kwargs: requests.append((args, kwargs)),
    )
    monkeypatch.setattr(
        chat,
        "_start_request",
        lambda directive, status_only: submitted.append((directive, status_only)),
    )
    chat.input_field.setText("audita o projeto")
    chat._handle_command()

    assert len(requests) == 1
    assert requests[0][0][0:3] == (
        "send-user-entry",
        "POST",
        "/mobile/threads/thread-existing/entries",
    )
    assert submitted == []

    chat._on_conversation_request_completed("send-user-entry", {"message": {}}, "")

    assert submitted == [("audita o projeto", False)]
    assert chat.history[-1]["sender"] == "Tu"
    chat.close()


def test_transcript_entries_are_written_sequentially(qt_app, monkeypatch):
    chat = CommandConsoleWidget()
    calls = []
    monkeypatch.setattr(
        chat,
        "_conversation_request",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    chat._persist_transcript_entry("thread-1", "assistant", "primeira resposta")
    chat._persist_transcript_entry("thread-1", "system", "estado da missão")

    assert len(calls) == 1
    assert calls[0][0][0] == "transcript-entry"

    chat._on_conversation_request_completed("transcript-entry", {"ok": True}, "")

    assert len(calls) == 2
    assert calls[1][1]["payload"]["content"] == "estado da missão"
    chat.close()



def test_desktop_history_search_uses_next_offset(qt_app, monkeypatch):
    chat = CommandConsoleWidget()
    calls = []
    monkeypatch.setattr(
        chat,
        "_conversation_request",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    chat.search_field.setText("DGM")
    chat._search_threads()

    assert calls[0][1]["params"] == {"q": "DGM", "limit": 25, "offset": 0}
    chat._on_conversation_request_completed(
        "thread-search",
        {"results": [], "total_count": 30, "next_offset": 25, "has_more": True},
        "",
    )
    assert chat.search_more_btn.isEnabled()

    chat._search_more_threads()
    assert calls[1][1]["params"] == {"q": "DGM", "limit": 25, "offset": 25}
    chat.close()



def test_history_navigation_is_disabled_during_mission(qt_app):
    chat = CommandConsoleWidget()

    class RunningWorker:
        @staticmethod
        def isRunning():
            return True

    chat._worker = RunningWorker()
    chat._refresh_controls()

    assert not chat.new_thread_btn.isEnabled()
    assert not chat.search_field.isEnabled()
    assert not chat.search_btn.isEnabled()
    assert not chat.thread_list.isEnabled()
    assert not chat.send_btn.isEnabled()
    chat._worker = None
    chat.close()


def test_failed_transcript_persistence_never_dispatches_mission(qt_app, monkeypatch):
    chat = CommandConsoleWidget()
    submitted = []
    monkeypatch.setattr(
        chat,
        "_start_request",
        lambda *args, **kwargs: submitted.append((args, kwargs)),
    )
    chat._pending_directive = "executa a tarefa"
    chat._on_conversation_request_completed(
        "send-user-entry", None, "erro de persistência"
    )

    assert submitted == []
    assert chat._pending_directive is None
    assert "missão não foi enviada" in chat.history[-1]["text"]
    chat.close()


def test_project_status_question_uses_dossier_endpoint_without_creating_mission(qt_app, monkeypatch):
    chat = CommandConsoleWidget()
    chat._active_thread_id = "thread-project"
    requests = []
    submitted = []
    monkeypatch.setattr(
        chat, "_conversation_request",
        lambda *args, **kwargs: requests.append((args, kwargs)),
    )
    monkeypatch.setattr(
        chat, "_start_request",
        lambda *args, **kwargs: submitted.append((args, kwargs)),
    )
    chat._pending_directive = "Qual é o estado do VAZÃO EVSE?"
    chat._on_conversation_request_completed("send-user-entry", {"message": {}}, "")

    assert requests[0][0][0:3] == (
        "project-dossier", "GET", "/runtime/repository-learning/dossier"
    )
    assert requests[0][1]["params"] == {"query": "Qual é o estado do VAZÃO EVSE?"}
    assert submitted == []
    assert chat._project_dossier_active is True
    chat.close()


def test_project_dossier_response_distinguishes_ambiguous_and_not_found():
    ambiguous, kind = CommandConsoleWidget._format_project_dossier_response({
        "status": "ambiguous",
        "candidates": [
            {"project_id": "one", "name": "Projeto Um"},
            {"project_id": "two", "name": "Projeto Dois"},
        ],
    })
    assert kind == "system"
    assert "Não escolhi nenhum" in ambiguous
    assert "one" in ambiguous and "two" in ambiguous

    missing, kind = CommandConsoleWidget._format_project_dossier_response({
        "status": "not_found", "query": "Projeto inexistente"
    })
    assert kind == "system"
    assert "Não foi criada nem enviada qualquer missão" in missing


def test_project_dossier_response_marks_git_as_persisted_not_live():
    message, kind = CommandConsoleWidget._format_project_dossier_response({
        "project": {"project_id": "evse", "name": "VAZÃO EVSE"},
        "coverage": {"vault_conversations_total": 3, "by_provider": {"chatgpt": 2}},
        "repository": {
            "local_inventory": {
                "match_status": "exact_path_match",
                "repositories": [{
                    "branch": "main", "head_sha": "a" * 40,
                    "working_tree_dirty": False, "scan_status": "complete",
                    "last_seen_at": "2026-11-13T10:00:00Z",
                }],
            },
            "snapshots": [],
            "conversation_linked_references": [],
            "conversation_linked_code_candidates": [],
        },
        "status": {"classification": "evidence_partial"},
        "static_audit": None,
    })
    assert kind == "info"
    assert "VAZÃO EVSE" in message
    assert "última observação persistida" in message
    assert "não uma verificação em tempo real" in message


def test_project_dossier_intent_is_limited_to_status_queries():
    assert CommandConsoleWidget._is_project_dossier_request(
        "Qual é o estado do VAZÃO EVSE?"
    )
    assert CommandConsoleWidget._is_project_dossier_request(
        "Mostra o dossier do DGM-MAT"
    )
    assert not CommandConsoleWidget._is_project_dossier_request(
        "Audita o projeto VAZÃO EVSE e corrige os erros"
    )
    assert not CommandConsoleWidget._is_project_dossier_request("runtime status")


def test_dossier_worker_uses_authenticated_runtime_origin_and_query(qt_app, monkeypatch):
    import threading

    calls = []
    class Response:
        status_code = 200
        @staticmethod
        def json():
            return {"status": "not_found", "query": "Projeto inexistente"}

    def fake_request(method, url, **kwargs):
        calls.append((threading.get_ident(), method, url, kwargs))
        return Response()

    monkeypatch.setattr(
        "cockpit.widgets.command_console.authenticated_request", fake_request
    )
    worker = _ConversationRequestWorker(
        "http://127.0.0.1:8181/runtime",
        "project-dossier",
        "GET",
        "/runtime/repository-learning/dossier",
        params={"query": "Qual é o estado do VAZÃO EVSE?"},
    )
    emitted = []
    worker.completed.connect(lambda *args: emitted.append(args))
    gui_thread = threading.get_ident()
    worker.start()
    assert worker.wait(3000)
    qt_app.processEvents()

    assert calls[0][0] != gui_thread
    assert calls[0][1:3] == (
        "GET",
        "http://127.0.0.1:8181/runtime/repository-learning/dossier",
    )
    assert calls[0][3]["params"] == {"query": "Qual é o estado do VAZÃO EVSE?"}
    assert emitted == [(
        "project-dossier",
        {"status": "not_found", "query": "Projeto inexistente"},
        "",
    )]
