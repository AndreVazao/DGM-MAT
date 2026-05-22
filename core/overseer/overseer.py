from shared.models.event import Event

from core.observability.logger import dgm_logger


class Overseer:

    def __init__(self):

        self.processed_events = 0

    def observe(self, event: Event):

        self.processed_events += 1

        dgm_logger.info(
            f"[OVERSEER] observed "
            f"{event.event_type}"
        )
