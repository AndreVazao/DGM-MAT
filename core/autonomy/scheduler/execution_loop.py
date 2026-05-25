import time
import threading
from core.observability.logger import dgm_logger
from core.autonomy.scheduler.task_queue import PersistentTaskQueue
from core.autonomy.scheduler.retry_manager import RetryManager

class ExecutionLoop:
    """
    Hardened task execution loop.
    """
    def __init__(self, task_queue: PersistentTaskQueue, retry_manager: RetryManager):
        self.queue = task_queue
        self.retry_manager = retry_manager
        self._running = False
        self._thread = None

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        dgm_logger.info("ExecutionLoop: Task processing loop started.")

    def _loop(self):
        while self._running:
            try:
                task = self.queue.lease_task()
                if task:
                    self._execute_task(task)
                else:
                    # Idle sleep
                    time.sleep(5)
            except Exception as e:
                dgm_logger.error(f"ExecutionLoop: Critical loop error: {e}")
                time.sleep(10) # Cooling sleep

    def _execute_task(self, task: dict):
        dgm_logger.info(f"ExecutionLoop: Executing {task['id']} ({task['type']})")
        try:
            # Simulation of delegated execution
            time.sleep(0.5)
            self.queue.complete_task(task["id"])
        except Exception as e:
            dgm_logger.error(f"ExecutionLoop: Task {task['id']} failed: {e}")
            retry = self.retry_manager.should_retry(task.get("retry_count", 0))
            self.queue.fail_task(task["id"], str(e), retry=retry)

    def stop(self):
        dgm_logger.info("ExecutionLoop: Stopping...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
