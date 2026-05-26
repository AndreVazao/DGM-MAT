import pytest
import os
from core.autonomy.work_queue import WorkQueue

def test_work_queue_persistence(tmp_path):
    db_file = tmp_path / "tasks.db"
    queue = WorkQueue(db_path=str(db_file))
    task_id = "test_id_123"
    queue.add_task(task_id, "test_task", {"data": "val"}, priority=5)
    task = queue.lease_task()
    assert task is not None
    assert task["id"] == task_id
