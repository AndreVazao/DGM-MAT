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
