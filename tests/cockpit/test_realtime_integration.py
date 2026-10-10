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
    assert window.runtime_status == "running"
    assert window.governance_widget is not None

def test_execution_feed_dispatch(app):
    window = MainWindow()
    test_msg = {
        "type": "execution_event",
        "payload": {"event": "INFO", "task_id": "T1", "message": "Test Task"}
    }
    window.dispatch_message(test_msg)
    assert window.execution_feed.feed_list.count() == 1
    assert "Test Task" in window.execution_feed.feed_list.item(0).text()


def test_realtime_state_updates_are_dispatched_through_qt_signals(app):
    window = MainWindow()
    window._queue_server_message({
        "type": "state_update",
        "data": {
            "runtime_status": "running",
            "system_state": "READY",
            "boot_phase": "OPERATIONAL",
            "node_status": "ONLINE",
            "is_degraded": False,
            "missions": {},
        },
    })
    app.processEvents()
    assert window.system_state == "READY"
    assert window.is_connected is False
    window.close()


def test_realtime_client_stop_before_connect_is_final():
    import asyncio
    from cockpit.streaming.realtime_client import RealtimeClient

    client = RealtimeClient("ws://127.0.0.1:9/ws")
    client.stop()
    asyncio.run(client.connect())
    assert client._stop_requested is True
    assert client.is_connected is False
