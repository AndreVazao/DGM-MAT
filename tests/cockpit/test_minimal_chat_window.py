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
