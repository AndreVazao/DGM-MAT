import time
from collections import defaultdict
from queue import Queue
from threading import Lock, Thread
from typing import Callable

from shared.models.event import Event
from core.validation.event_validator import (
    EventValidator,
)
from core.observability.logger import (
    dgm_logger,
)
from core.storage.event_store import (
    EventStore,
)
from core.observability.event_stream import (
    stream_event,
)

class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.queue = Queue()
        self.lock = Lock()
        self.running = False

    def subscribe(
        self,
        event_type: str,
        callback: Callable,
    ):
        with self.lock:
            self.subscribers[event_type].append(
                callback
            )
        dgm_logger.info(
            f"Subscriber added -> {event_type}"
        )

    def publish(self, event: Event):
        EventValidator.validate(event)
        EventStore.persist(event)
        stream_event(event)
        self.queue.put(event)
        dgm_logger.info(
            f"Event published -> "
            f"{event.event_type}"
        )

    def start(self):
        self.running = True
        thread = Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        while self.running:
            self.process()
            time.sleep(0.1)

    def process(self):
        while not self.queue.empty():
            event = self.queue.get()

            with self.lock:
                callbacks = list(self.subscribers.get(
                    event.event_type,
                    []
                ))

            for callback in callbacks:
                try:
                    callback(event)
                except Exception as exc:
                    dgm_logger.error(
                        f"Handler failure: {exc}"
                    )
