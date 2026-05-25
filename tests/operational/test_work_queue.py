import pytest
import os
import shutil
from core.autonomy.work_queue import WorkQueue
from core.storage.storage_manager import storage_manager

def test_work_queue_persistence():
    queue = WorkQueue()
    task_id = queue.add_task("test_task", {"data": "val"})

    # Reload queue
    queue2 = WorkQueue()
    task = next((t for t in queue2.tasks if t.id == task_id), None)
    assert task is not None
    assert task.type == "test_task"
