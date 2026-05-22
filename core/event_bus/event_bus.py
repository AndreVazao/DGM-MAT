from collections import defaultdict
from queue import Queue
from threading import Lock
from typing import Callable

from shared.models.event import Event

from core.validation.event_validator import (
    EventValidator,
)

from core.observability.logger import dgm_logger


class EventBus:

    def __init__(self):

        self.subscribers = defaultdict(list)

        self.queue = Queue()

        self.lock = Lock()

    def subscribe(
        self,
        event_type: str,
        callback: Callable,
    ) -> None:

        with self.lock:
            self.subscribers[event_type].append(callback)

        dgm_logger.info(
            f"Subscriber added -> {event_type}"
        )

    def publish(self, event: Event) -> None:

        EventValidator.validate(event)

        self.queue.put(event)

        dgm_logger.info(
            f"Event published -> {event.event_type}"
        )

    def process(self) -> None:

        while not self.queue.empty():

            event = self.queue.get()

            callbacks = self.subscribers.get(
                event.event_type,
                []
            )

            if not callbacks:
                dgm_logger.warning(
                    f"No subscribers for event "
                    f"{event.event_type}"
                )

            for callback in callbacks:

                try:
                    callback(event)

                except Exception as exc:

                    dgm_logger.error(
                        f"Event handler failure: {exc}"
                    )
