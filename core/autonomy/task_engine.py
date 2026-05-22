from core.autonomy.task_queue import (
    TaskQueue,
)

from core.autonomy.task_planner import (
    TaskPlanner,
)


class TaskEngine:

    def __init__(self):

        self.queue = TaskQueue()

    def analyze_issue(
        self,
        issue_type: str,
        description: str,
    ):

        task = (
            TaskPlanner()
            .create_task(
                issue_type,
                description,
            )
        )

        self.queue.add_task(task)

        print("\n")

        print("=" * 60)

        print("AUTONOMOUS TASK CREATED")

        print("=" * 60)

        print(task)
