import time
import random
from collections import defaultdict
from queue import Queue
from threading import Lock, Thread
from typing import Callable, Optional, Set

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
    def __init__(self, governance_engine=None):
        self.subscribers = defaultdict(list)
        self.queue = Queue()
        self.lock = Lock()
        self.running = False
        self.governance_engine = governance_engine

        # Hardening
        self.seen_event_ids: Set[str] = set()
        self.max_seen_history = 1000
        self.max_propagation_depth = 20

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
        # 1. Duplicate Suppression (Requirement 11)
        if event.id in self.seen_event_ids:
            dgm_logger.debug(f"EventBus: Suppressing duplicate event {event.id}")
            return

        with self.lock:
            self.seen_event_ids.add(event.id)
            if len(self.seen_event_ids) > self.max_seen_history:
                # Poor man's LRU/Pruning
                self.seen_event_ids = set(list(self.seen_event_ids)[-self.max_seen_history:])

        # 2. Propagation Depth Enforcement (Requirement 2)
        if event.depth > self.max_propagation_depth:
            dgm_logger.error(f"EventBus: MAX PROPAGATION DEPTH REACHED ({event.depth}). Dropping event {event.event_type}.")
            return

        # 3. Apply governance if engine is available
        if self.governance_engine:
            # Overload Sampling (Requirement 2)
            if self.governance_engine.degradation_controller.is_degraded():
                if event.priority == "low" and random.random() > 0.5:
                    dgm_logger.info(f"EventBus: Sampling event {event.event_type} under overload.")
                    return

            if not self.governance_engine.govern_event(event):
                dgm_logger.warning(f"Event dropped by governance: {event.event_type} (depth: {event.depth})")
                return

        EventValidator.validate(event)
        EventStore.persist(event)
        stream_event(event)
        self.queue.put(event)
        dgm_logger.info(
            f"Event published -> "
            f"{event.event_type} (trace_id: {event.trace_id}, depth: {event.depth})"
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
                # Wildcard filtering and subscriber retrieval
                callbacks = list(self.subscribers.get(event.event_type, []))
                # Only allow specific modules for wildcard if needed, but for now strict
                callbacks.extend(self.subscribers.get("*", []))

            for callback in callbacks:
                try:
                    callback(event)
                except Exception as exc:
                    dgm_logger.error(
                        f"Handler failure for {event.event_type}: {exc}"
                    )

    def create_child_event(self, parent_event: Event, event_type: str, target: str, payload: dict = None) -> Event:
        """Helper to create a child event with incremented depth and linked trace_id."""
        return Event(
            source=parent_event.target,
            target=target,
            event_type=event_type,
            payload=payload or {},
            trace_id=parent_event.trace_id,
            parent_trace_id=parent_event.trace_id,
            depth=parent_event.depth + 1,
            priority=parent_event.priority,
            ecosystem=parent_event.ecosystem
        )
