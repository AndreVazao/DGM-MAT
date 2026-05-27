import pytest
from cockpit.main_window import MainWindow
from PySide6.QtWidgets import QApplication
import sys

@pytest.fixture
def app():
    return QApplication.instance() or QApplication(sys.argv)

def test_mainwindow_dispatch(app):
    window = MainWindow()
    # Mock data
    test_msg = {
        "type": "runtime_status",
        "payload": {"status": "running", "cpu": 50, "memory": 60}
    }
    window.dispatch_message(test_msg)
    assert window.operational_dashboard.status_label.text() == "System Status: RUNNING"
    assert window.operational_dashboard.cpu_bar.value() == 50

def test_execution_feed_dispatch(app):
    window = MainWindow()
    test_msg = {
        "type": "execution_event",
        "payload": {"event": "INFO", "task_id": "T1", "message": "Test Task"}
    }
    window.dispatch_message(test_msg)
    assert window.execution_feed.feed_list.count() == 1
    assert "Test Task" in window.execution_feed.feed_list.item(0).text()
