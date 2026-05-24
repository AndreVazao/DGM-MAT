import time
from typing import List, Callable
from core.observability.logger import dgm_logger

class AutonomousScheduler:
    """
    Handles periodic and scheduled tasks.
    """
    def __init__(self):
        self.jobs = []

    def schedule(self, func: Callable, interval_seconds: int):
        self.jobs.append({
            "func": func,
            "interval": interval_seconds,
            "last_run": 0
        })

    def run_pending(self):
        current_time = time.time()
        for job in self.jobs:
            if current_time - job["last_run"] >= job["interval"]:
                dgm_logger.info(f"Scheduler: Running job {job['func'].__name__}")
                try:
                    job["func"]()
                except Exception as e:
                    dgm_logger.error(f"Scheduler: Job failed: {e}")
                job["last_run"] = current_time
