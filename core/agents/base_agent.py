from abc import ABC, abstractmethod

from shared.models.event import Event

from core.observability.logger import dgm_logger


class BaseAgent(ABC):

    def __init__(self, agent_id: str):

        self.agent_id = agent_id

        self.health = "healthy"

    @abstractmethod
    def handle_event(self, event: Event) -> None:
        pass

    def emit_log(self, message: str):

        dgm_logger.info(
            f"[{self.agent_id}] {message}"
        )
