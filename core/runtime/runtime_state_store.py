import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime
from core.observability.logger import dgm_logger

class StateEvents(Enum):
    PROVIDER_UPDATED = "provider_updated"
    MISSION_UPDATED = "mission_updated"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    FEDERATION_SYNC = "federation_sync"
    WEBSOCKET_CLIENT_CONNECTED = "websocket_client_connected"
    WEBSOCKET_CLIENT_DISCONNECTED = "websocket_client_disconnected"
    APPROVAL_REQUESTED = "approval_requested"
    TASK_UPDATED = "task_updated"
    MEMORY_STATS_UPDATED = "memory_stats_updated"
    COCKPIT_STATE_CHANGED = "cockpit_state_changed"

@dataclass
class RuntimeSnapshot:
    timestamp: float
    providers: Dict[str, Any] = field(default_factory=dict)
    missions: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    federation: Dict[str, Any] = field(default_factory=dict)
    websocket: Dict[str, Any] = field(default_factory=dict)
    approvals: List[Any] = field(default_factory=list)
    tasks: Dict[str, Any] = field(default_factory=dict)
    memory_stats: Dict[str, Any] = field(default_factory=dict)
    cockpit: Dict[str, Any] = field(default_factory=dict)

class StateReducer:
    @staticmethod
    def reduce(state: RuntimeSnapshot, event_type: StateEvents, payload: Any) -> RuntimeSnapshot:
        """
        Redux-style reducer for state updates.
        Returns a new snapshot or modifies in place if controlled.
        For Phase 42.3-LITE, we'll perform a partial update on a copy.
        """
        # Shallow copy for the snapshot
        new_state = RuntimeSnapshot(
            timestamp=time.time(),
            providers=state.providers.copy(),
            missions=state.missions.copy(),
            agents=state.agents.copy(),
            federation=state.federation.copy(),
            websocket=state.websocket.copy(),
            approvals=list(state.approvals),
            tasks=state.tasks.copy(),
            memory_stats=state.memory_stats.copy(),
            cockpit=state.cockpit.copy()
        )

        if event_type == StateEvents.PROVIDER_UPDATED:
            provider_name = payload.get("name")
            if provider_name:
                new_state.providers[provider_name] = payload

        elif event_type == StateEvents.MISSION_UPDATED:
            mission_id = payload.get("id")
            if mission_id:
                new_state.missions[mission_id] = payload

        elif event_type == StateEvents.AGENT_STATUS_CHANGED:
            agent_id = payload.get("id")
            if agent_id:
                new_state.agents[agent_id] = payload

        elif event_type == StateEvents.TASK_UPDATED:
            task_id = payload.get("id")
            if task_id:
                new_state.tasks[task_id] = payload

        elif event_type == StateEvents.MEMORY_STATS_UPDATED:
            new_state.memory_stats.update(payload)

        elif event_type == StateEvents.COCKPIT_STATE_CHANGED:
            new_state.cockpit.update(payload)

        elif event_type == StateEvents.WEBSOCKET_CLIENT_CONNECTED:
            client_id = payload.get("id")
            new_state.websocket[client_id] = payload

        elif event_type == StateEvents.WEBSOCKET_CLIENT_DISCONNECTED:
            client_id = payload.get("id")
            if client_id in new_state.websocket:
                del new_state.websocket[client_id]

        return new_state

class RuntimeStateStore:
    """
    Single source of truth for the DGM-MAT runtime.
    Thread-safe implementation with event sourcing principles.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RuntimeStateStore, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.state = RuntimeSnapshot(timestamp=time.time())
        self.lock = threading.Lock()
        self.subscribers: List[Callable] = []
        self._initialized = True
        dgm_logger.info("RuntimeStateStore: Initialized.")

    def dispatch(self, event_type: StateEvents, payload: Any):
        """Dispatches an event to update the state."""
        with self.lock:
            old_state = self.state
            self.state = StateReducer.reduce(self.state, event_type, payload)
            dgm_logger.debug(f"RuntimeStateStore: State updated via {event_type.value}")

        self._notify_subscribers()

    def subscribe(self, callback: Callable):
        """Subscribes to state changes."""
        with self.lock:
            if callback not in self.subscribers:
                self.subscribers.append(callback)

    def _notify_subscribers(self):
        """Notifies all subscribers of a state change."""
        snapshot = self.get_snapshot()
        for callback in self.subscribers:
            try:
                callback(snapshot)
            except Exception as e:
                dgm_logger.error(f"RuntimeStateStore: Subscriber notification failed: {e}")

    def get_snapshot(self) -> RuntimeSnapshot:
        """Returns the current state snapshot."""
        with self.lock:
            return self.state

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the state for API/Websocket export."""
        return asdict(self.get_snapshot())

# Global singleton
state_store = RuntimeStateStore()
