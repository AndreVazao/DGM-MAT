from typing import List, Dict, Any
from core.observability.logger import dgm_logger
from core.autonomy.task_generator import TaskGenerator

class ExecutionDirector:
    def __init__(self):
        self.task_generator = TaskGenerator()

    def assign_tasks(self, objectives: List[Dict[str, Any]]) -> List[str]:
        dgm_logger.info("ExecutionDirector: Assigning tasks for objectives.")
        task_ids = []
        for obj in objectives:
            task = self.task_generator.create_task(
                title=f"Resolve {obj['target']}",
                description=f"Automated task to address {obj['target']}",
                priority=obj['priority'],
                origin="autonomy_loop",
                task_category="autonomous_improvement"
            )
            task_ids.append(task.task_id)
        return task_ids
