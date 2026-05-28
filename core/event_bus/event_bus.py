import time
import random
from collections import defaultdict
from queue import PriorityQueue, Queue
from threading import Lock, Thread
from typing import Callable, Optional, Set, Dict, List
from datetime import datetime

from shared.models.event import Event
from shared.enums.event_priority import EventPriority
from core.validation.event_validator import EventValidator
from core.observability.logger import dgm_logger
from core.storage.event_store import EventStore
from core.observability.event_stream import stream_event

class EventBus:
    """
    Event Bus V2 - Distributed Runtime Stabilization (Phase 42.3-LITE)
    Features: Priority Routing, DLQ, Deduplication, Throttling, TTL.
    """
    def __init__(self, governance_engine=None):
        self.subscribers = defaultdict(list)
        # Use PriorityQueue to handle events by priority
        # PriorityQueue expects (priority_value, item) where lower value is higher priority
        self.queue = PriorityQueue()
        self.dlq = Queue() # Dead Letter Queue
        self.lock = Lock()
        self.running = False
        self.governance_engine = governance_engine

        # Hardening & Stabilization
        self.seen_event_ids: Set[str] = set()
        self.max_seen_history = 2000
        self.max_propagation_depth = 25

        # Throttling
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.last_throttle_reset = time.time()
        self.throttle_threshold = 50 # Max events per second for same type

    def _get_priority_value(self, priority: EventPriority) -> int:
        mapping = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.MEDIUM: 2,
            EventPriority.LOW: 3
        }
        return mapping.get(priority, 3)

    def subscribe(self, event_type: str, callback: Callable):
        with self.lock:
            self.subscribers[event_type].append(callback)
        dgm_logger.info(f"EventBus V2: Subscriber added -> {event_type}")

    def publish(self, event: Event):
        # 1. Deduplication
        if event.id in self.seen_event_ids:
            return

        with self.lock:
            self.seen_event_ids.add(event.id)
            if len(self.seen_event_ids) > self.max_seen_history:
                self.seen_event_ids = set(list(self.seen_event_ids)[-self.max_seen_history:])

        # 2. TTL Check
        age = (datetime.now() - event.timestamp).total_seconds()
        if age > event.ttl:
            dgm_logger.warning(f"EventBus V2: Event {event.id} expired (TTL: {event.ttl}s). Dropping.")
            return

        # 3. Throttling
        now = time.time()
        if now - self.last_throttle_reset > 1.0:
            self.event_counts.clear()
            self.last_throttle_reset = now

        self.event_counts[event.event_type] += 1
        if self.event_counts[event.event_type] > self.throttle_threshold:
            if event.priority != EventPriority.CRITICAL:
                dgm_logger.warning(f"EventBus V2: Throttling event type {event.event_type}")
                return

        # 4. Propagation Depth
        if event.depth > self.max_propagation_depth:
            dgm_logger.error(f"EventBus V2: MAX DEPTH reached for {event.id}. Sending to DLQ.")
            self.dlq.put(event)
            return

        # 5. Governance
        if self.governance_engine:
            if not self.governance_engine.govern_event(event):
                return

        try:
            EventValidator.validate(event)
            EventStore.persist(event)
            stream_event(event)

            # Put in PriorityQueue
            priority_val = self._get_priority_value(event.priority)
            self.queue.put((priority_val, time.time(), event))

            dgm_logger.debug(f"EventBus V2: Published {event.event_type} (priority: {event.priority})")
        except Exception as e:
            dgm_logger.error(f"EventBus V2: Publication failed for {event.id}: {e}")
            self.dlq.put(event)

    def start(self):
        self.running = True
        thread = Thread(target=self._run, daemon=True)
        thread.start()
        dgm_logger.info("EventBus V2: Daemon thread started.")

    def _run(self):
        while self.running:
            try:
                self.process()
                time.sleep(0.01) # Reduced sleep for high concurrency
            except Exception as e:
                dgm_logger.error(f"EventBus V2: Loop error: {e}")

    def process(self):
        while not self.queue.empty():
            _, _, event = self.queue.get()

            with self.lock:
                callbacks = list(self.subscribers.get(event.event_type, []))
                callbacks.extend(self.subscribers.get("*", []))

            for callback in callbacks:
                try:
                    callback(event)
                except Exception as exc:
                    dgm_logger.error(f"EventBus V2: Handler failure for {event.event_type}: {exc}")
                    # In a real system, we might retry or send to a handler-specific DLQ

    def create_child_event(self, parent_event: Event, event_type: str, target: str, payload: dict = None) -> Event:
        return Event(
            source=parent_event.target,
            target=target,
            event_type=event_type,
            payload=payload or {},
            trace_id=parent_event.trace_id,
            parent_trace_id=parent_event.trace_id,
            depth=parent_event.depth + 1,
            priority=parent_event.priority,
            scope=parent_event.scope,
            domain=parent_event.domain,
            ecosystem=parent_event.ecosystem
        )
