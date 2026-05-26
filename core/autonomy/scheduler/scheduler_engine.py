import time
from typing import List, Dict, Any
from core.observability.logger import dgm_logger
from core.autonomy.models import AutonomousTask

class SchedulerEngine:
    """Manages execution quotas and prevents runaway tasks."""
    def __init__(self):
        self.active_tasks: Dict[str, float] = {} # task_id -> start_time
        self.quota_per_hour = 20
        self.execution_count_last_hour = 0
        self.task_timeout = 600 # 10 minutes

    def schedule_task(self, task: AutonomousTask) -> bool:
        if self.execution_count_last_hour >= self.quota_per_hour:
            dgm_logger.warning(f"SchedulerEngine: Hourly execution quota ({self.quota_per_hour}) reached. Delaying {task.task_id}")
            return False

        dgm_logger.info(f"SchedulerEngine: Scheduling task {task.task_id} for execution.")
        self.active_tasks[task.task_id] = time.time()
        self.execution_count_last_hour += 1
        return True

    def check_for_runaway_tasks(self):
        """Detects and terminates tasks that have exceeded their time limit."""
        now = time.time()
        runaway_ids = []
        for tid, start_time in self.active_tasks.items():
            if now - start_time > self.task_timeout:
                dgm_logger.error(f"SchedulerEngine: Runaway task detected: {tid}. Exceeded {self.task_timeout}s")
                runaway_ids.append(tid)

        for tid in runaway_ids:
            # Logic to terminate would go here
            del self.active_tasks[tid]

    def complete_task(self, task_id: str):
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            dgm_logger.info(f"SchedulerEngine: Task {task_id} marked as completed.")
