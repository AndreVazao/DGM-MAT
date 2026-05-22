from shared.models.event import Event

from core.agents.base_agent import (
    BaseAgent,
)

from core.autonomy.task_engine import (
    TaskEngine,
)


class AutonomyAgent(BaseAgent):

    def handle_event(
        self,
        event: Event,
    ):

        self.emit_log(
            "Analyzing ecosystem..."
        )

        TaskEngine().analyze_issue(
            "repo",
            "Potential duplicated systems",
        )
