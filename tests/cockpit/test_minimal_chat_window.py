import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import requests
from PySide6.QtWidgets import QApplication

from cockpit.minimal_chat_window import MinimalChatWindow
from cockpit.widgets.command_console import (
    CommandConsoleWidget,
    _RuntimeRequestWorker,
)


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_default_cockpit_is_single_chat_view(qt_app):
    window = MinimalChatWindow()

    assert window.windowTitle() == "DGM-MAT — Chat"
    assert isinstance(window.centralWidget(), CommandConsoleWidget)
    assert window.centralWidget().input_field is not None
    assert window.centralWidget().send_btn is not None

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
