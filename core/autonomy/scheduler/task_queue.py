import sqlite3
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class PersistentTaskQueue:
    def __init__(self, db_path: Optional[str] = None):
        # Requirement 2: Use persistent absolute directories
        if not db_path:
            self.db_path = storage_manager.get_path("tasks", "tasks.db")
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, type TEXT, payload TEXT, priority INTEGER, status TEXT, created_at REAL, retry_count INTEGER, locked_until REAL, last_error TEXT)")
        except sqlite3.Error as e:
            dgm_logger.error(f"TaskQueue: Failed to initialize database at {self.db_path}: {e}")

    def add_task(self, task_id: str, task_type: str, payload: dict, priority: int = 10):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (task_id, task_type, json.dumps(payload), priority, "pending", time.time(), 0, 0, None))
        except sqlite3.Error as e:
            dgm_logger.error(f"TaskQueue: Failed to add task {task_id}: {e}")

    def lease_task(self) -> Optional[dict]:
        now = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM tasks WHERE status='pending' AND locked_until < ? ORDER BY priority DESC, created_at ASC LIMIT 1", (now,)).fetchone()
                if row:
                    t = dict(row)
                    t["payload"] = json.loads(t["payload"])
                    t["status"] = "running"
                    conn.execute("UPDATE tasks SET status='running', locked_until=? WHERE id=?", (now+600, t["id"]))
                    return t
        except sqlite3.Error as e:
            dgm_logger.error(f"TaskQueue: Failed to lease task: {e}")
        return None

    def complete_task(self, tid):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE tasks SET status='completed' WHERE id=?", (tid,))
        except sqlite3.Error as e:
            dgm_logger.error(f"TaskQueue: Failed to complete task {tid}: {e}")

    def fail_task(self, tid, err, retry=True):
        try:
            with sqlite3.connect(self.db_path) as conn:
                status = "pending" if retry else "failed"
                conn.execute("UPDATE tasks SET status=?, last_error=?, locked_until=? WHERE id=?", (status, err, time.time()+60, tid))
        except sqlite3.Error as e:
            dgm_logger.error(f"TaskQueue: Failed to fail task {tid}: {e}")
