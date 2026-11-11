from threading import Event, Thread

from core.runtime.safe_action_queue import SafeActionQueue


def test_stop_consumer_reports_active_worker_and_waits_until_it_exits():
    queue = object.__new__(SafeActionQueue)
    queue._stop_event = Event()
    started = Event()
    release = Event()

    def worker():
        started.set()
        release.wait()

    queue._worker_thread = Thread(target=worker, name="test-safe-action-queue")
    queue._worker_thread.start()
    assert started.wait(1.0)

    assert queue.stop_consumer(timeout=0.001) is False
    assert queue._worker_thread.is_alive()

    release.set()
    assert queue.stop_consumer(timeout=1.0) is True
    assert not queue._worker_thread.is_alive()
