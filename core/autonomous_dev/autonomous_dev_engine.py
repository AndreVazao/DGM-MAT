from core.observability.logger import dgm_logger
from core.autonomous_dev.task_generator import TaskGenerator
from core.autonomous_dev.roadmap_executor import RoadmapExecutor

class AutonomousDevEngine:
    """
    Orchestrates the autonomous development loop.
    """
    def __init__(self):
        self.task_generator = TaskGenerator()
        self.roadmap_executor = RoadmapExecutor()

    def run_development_cycle(self):
        dgm_logger.info("AutonomousDevEngine: Starting development cycle")
        tasks = self.task_generator.generate_tasks()
        for task in tasks:
            self.roadmap_executor.execute_task(task)
