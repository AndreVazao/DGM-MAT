from dgm_contracts import Event, NullTaskService, TaskService

from core.agents.base_agent import BaseAgent


class AutonomyAgent(BaseAgent):
    def __init__(self, agent_id: str, logger=None, task_service: TaskService | None = None):
        super().__init__(agent_id, logger)
        self.task_service = task_service or NullTaskService()

    def handle_event(
        self,
        event: Event,
    ):

        self.emit_log(
            "Analyzing ecosystem..."
        )

        self.task_service.analyze_issue(
            "repo",
            "Potential duplicated systems",
        )
