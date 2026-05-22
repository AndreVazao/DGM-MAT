from uuid import uuid4

from core.autonomy.models import (
    AutonomousTask,
)

from core.autonomy.priority_engine import (
    PriorityEngine,
)

from core.autonomy.worker_allocator import (
    WorkerAllocator,
)


class TaskPlanner:

    def create_task(
        self,
        issue_type: str,
        description: str,
    ):

        priority = (
            PriorityEngine()
            .calculate(issue_type)
        )

        agent = (
            WorkerAllocator()
            .allocate(issue_type)
        )

        return AutonomousTask(
            task_id=str(uuid4()),
            title=f"{issue_type} issue",
            description=description,
            priority=priority,
            assigned_agent=agent,
            status="pending",
        )
