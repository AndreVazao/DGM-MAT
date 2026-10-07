from abc import ABC, abstractmethod

from dgm_contracts import AgentLogger, Event, NullAgentLogger


class BaseAgent(ABC):

    def __init__(self, agent_id: str, logger: AgentLogger | None = None):
        self.agent_id = agent_id
        self.health = "healthy"
        self.logger = logger or NullAgentLogger()

    @abstractmethod
    def handle_event(self, event: Event) -> None:
        pass

    def emit_log(self, message: str):

        self.logger.info(f"[{self.agent_id}] {message}")
