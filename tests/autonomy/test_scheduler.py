import pytest
from core.autonomy.scheduler.task_queue import PersistentTaskQueue

def test_persistent_queue(tmp_path):
    db_path = tmp_path / "tasks.db"
    queue = PersistentTaskQueue(db_path=str(db_path))
    queue.add_task("task-1", "test", {"data": 1}, priority=10)
    task = queue.lease_task()
    assert task is not None
    assert task["id"] == "task-1"
    assert task["status"] == "running"
