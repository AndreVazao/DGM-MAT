from core.autonomy.task_queue import TaskQueue
from core.autonomy.task_planner import TaskPlanner

class TaskEngine:
    def __init__(self):
        self.queue = TaskQueue()

    def analyze_issue(self, issue_type: str, description: str, origin: str = "repo_analysis"):
        task = TaskPlanner().create_task(
            issue_type,
            description,
            origin=origin
        )
        self.queue.add_task(
            task_id=task.task_id,
            task_type=issue_type,
            payload=task.metadata,
            priority=task.priority
        )
