import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from cockpit.minimal_chat_window import MinimalChatWindow
from cockpit.widgets.command_console import CommandConsoleWidget


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


def test_mission_status_poll_uses_single_durable_checkpoint(monkeypatch):
    from cockpit.widgets import command_console

    calls = []

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "mission_id": "mission_b55c3887",
                "status": "QUEUED",
                "progress": 0,
                "action_id": 42,
                "action_status": "QUEUED",
                "result": None,
                "output": None,
            }

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Response()

    monkeypatch.setattr(command_console, "authenticated_request", fake_request)
    worker = command_console._RuntimeRequestWorker(
        "http://127.0.0.1:8181/runtime", "diagnostic", status_only=False
    )

    mission = worker._mission("mission_b55c3887")

    assert mission["mission_id"] == "mission_b55c3887"
    assert calls == [(
        "GET",
        "http://127.0.0.1:8181/runtime/missions/mission_b55c3887",
        {"timeout": (2, 8)},
    )]


def test_mission_status_poll_rejects_mismatched_checkpoint(monkeypatch):
    from cockpit.widgets import command_console

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"mission_id": "mission_ffffffff", "status": "COMPLETED"}

    monkeypatch.setattr(command_console, "authenticated_request", lambda *args, **kwargs: Response())
    worker = command_console._RuntimeRequestWorker(
        "http://127.0.0.1:8181/runtime", "diagnostic", status_only=False
    )

    with pytest.raises(ValueError, match="checkpoint de missão inválido"):
        worker._mission("mission_b55c3887")
