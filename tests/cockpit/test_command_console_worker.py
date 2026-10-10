# Path: C:\ProgramasGodMode\DGM-MAT\tests\cockpit\test_command_console_worker.py
import threading

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
