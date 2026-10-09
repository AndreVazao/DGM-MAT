# Path: C:\ProgramasGodMode\DGM-MAT\tests\unit\test_resource_monitor_lifecycle.py
import threading

from core.governance.resource_monitor import ResourceMonitor


def test_resource_monitor_stops_promptly_and_thread_exits():
    callback_called = threading.Event()
    monitor = ResourceMonitor(interval=30)
    monitor.start(callback=lambda snapshot: callback_called.set())
    assert callback_called.wait(3), "monitor did not emit its first snapshot"
    worker = monitor.thread

    # Repeated start must not create a second background worker.
    monitor.start(callback=lambda snapshot: callback_called.set())
    assert monitor.thread is worker

    assert monitor.stop(timeout=2) is True
    assert worker is not None
    assert not worker.is_alive()


def test_resource_monitor_can_restart_after_clean_stop():
    first = threading.Event()
    second = threading.Event()
    monitor = ResourceMonitor(interval=30)
    monitor.start(callback=lambda snapshot: first.set())
    assert first.wait(3)
    assert monitor.stop(timeout=2) is True

    monitor.start(callback=lambda snapshot: second.set())
    assert second.wait(3)
    assert monitor.stop(timeout=2) is True
