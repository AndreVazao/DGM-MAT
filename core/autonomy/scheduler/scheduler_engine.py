from core.autonomy.scheduler.task_queue import PersistentTaskQueue
from core.autonomy.scheduler.execution_loop import ExecutionLoop
from core.autonomy.scheduler.retry_manager import RetryManager
from core.autonomy.scheduler.priority_router import PriorityRouter
class SchedulerEngine:
    def __init__(self):
        self.queue = PersistentTaskQueue()
        self.loop = ExecutionLoop(self.queue, RetryManager())
        self.router = PriorityRouter()
    def schedule_task(self, tid, ttype, payload, prio=50):
        self.queue.add_task(tid, ttype, payload, self.router.resolve(ttype, prio))
