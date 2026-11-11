from threading import Event, Thread

from core.autonomy.repository_learning import RepositoryLearningService
from core.mobile_runtime.auto_help import AutoHelpWorker


def _assert_stop_waits_for_worker(worker_type):
    worker = object.__new__(worker_type)
    worker._stop = Event()
    started = Event()
    release = Event()

    def run():
        started.set()
        release.wait()

    worker._thread = Thread(target=run, name="test-background-worker")
    worker._thread.start()
    assert started.wait(1.0)

    assert worker.stop(timeout=0.001) is False
    assert worker._thread.is_alive()

    release.set()
    assert worker.stop(timeout=1.0) is True
    assert not worker._thread.is_alive()


def test_repository_learning_stop_reports_worker_completion():
    _assert_stop_waits_for_worker(RepositoryLearningService)


def test_auto_help_stop_reports_worker_completion():
    _assert_stop_waits_for_worker(AutoHelpWorker)
