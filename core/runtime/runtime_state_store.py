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
    REALITY_UPDATED = "reality_updated"
    HEALTH_UPDATED = "health_updated"
    DEGRADATION_UPDATED = "degradation_updated"
    QUEUE_UPDATED = "queue_updated"
    CONSUMER_STATUS_CHANGED = "consumer_status_changed"
    BOOT_PHASE_UPDATED = "boot_phase_updated"

@dataclass
class RuntimeTruthState:
    timestamp: float
    runtime_status: str = "starting"
    system_state: str = "INITIALIZING"  # Priority 3 requirement
    boot_phase: str = "STARTUP"        # Priority 3 requirement
    node_status: str = "UNKNOWN"       # Priority 3 requirement
    is_degraded: bool = False
    degradation: Dict[str, Any] = field(default_factory=dict)
    health: Dict[str, Any] = field(default_factory=dict)
    reality: Dict[str, Any] = field(default_factory=dict)
    providers: Dict[str, Any] = field(default_factory=dict)
    missions: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    federation: Dict[str, Any] = field(default_factory=dict)
    websocket: Dict[str, Any] = field(default_factory=dict)
    approvals: List[Any] = field(default_factory=list)
    tasks: Dict[str, Any] = field(default_factory=dict)
    memory_stats: Dict[str, Any] = field(default_factory=lambda: {
        "total_memories": 0,
        "consolidated": 0,
        "patterns_detected": 0
    })
    cockpit: Dict[str, Any] = field(default_factory=dict)
    queue: Dict[str, Any] = field(default_factory=dict)
    consumers: Dict[str, Any] = field(default_factory=dict)

class StateReducer:
    @staticmethod
    def reduce(state: RuntimeTruthState, event_type: StateEvents, payload: Any) -> RuntimeTruthState:
        """
        Redux-style reducer for state updates.
        Returns a new snapshot or modifies in place if controlled.
        """
        new_state = RuntimeTruthState(
            timestamp=time.time(),
            runtime_status=state.runtime_status,
            system_state=state.system_state,
            boot_phase=state.boot_phase,
            node_status=state.node_status,
            is_degraded=state.is_degraded,
            degradation=state.degradation.copy(),
            health=state.health.copy(),
            reality=state.reality.copy(),
            providers=state.providers.copy(),
            missions=state.missions.copy(),
            agents=state.agents.copy(),
            federation=state.federation.copy(),
            websocket=state.websocket.copy(),
            approvals=list(state.approvals),
            tasks=state.tasks.copy(),
            memory_stats=state.memory_stats.copy(),
            cockpit=state.cockpit.copy(),
            queue=state.queue.copy(),
            consumers=state.consumers.copy()
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

        elif event_type == StateEvents.BOOT_PHASE_UPDATED:
            new_state.boot_phase = payload.get("phase", new_state.boot_phase)
            if "status" in payload:
                new_state.node_status = payload["status"]

        elif event_type == StateEvents.MEMORY_STATS_UPDATED:
            new_state.memory_stats.update(payload)

        elif event_type == StateEvents.COCKPIT_STATE_CHANGED:
            new_state.cockpit.update(payload)
            if "runtime_status" in payload:
                new_state.runtime_status = payload["runtime_status"]
                new_state.system_state = payload["runtime_status"].upper()
            if "is_degraded" in payload:
                new_state.is_degraded = payload["is_degraded"]

        elif event_type == StateEvents.REALITY_UPDATED:
            new_state.reality.update(payload)

        elif event_type == StateEvents.HEALTH_UPDATED:
            new_state.health.update(payload)

        elif event_type == StateEvents.DEGRADATION_UPDATED:
            new_state.degradation.update(payload)
            new_state.is_degraded = payload.get("is_degraded", new_state.is_degraded)

        elif event_type == StateEvents.WEBSOCKET_CLIENT_CONNECTED:
            client_id = payload.get("id")
            new_state.websocket[client_id] = payload

        elif event_type == StateEvents.WEBSOCKET_CLIENT_DISCONNECTED:
            client_id = payload.get("id")
            if client_id in new_state.websocket:
                del new_state.websocket[client_id]

        elif event_type == StateEvents.QUEUE_UPDATED:
            new_state.queue.update(payload)

        elif event_type == StateEvents.CONSUMER_STATUS_CHANGED:
            consumer_id = payload.get("id")
            if consumer_id:
                new_state.consumers[consumer_id] = payload

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

        self.state = RuntimeTruthState(timestamp=time.time())
        self.lock = threading.Lock()
        self.subscribers: List[Callable] = []
        self._initialized = True
        dgm_logger.info("RuntimeStateStore: Initialized with RuntimeTruthState.")

    def dispatch(self, event_type: StateEvents, payload: Any):
        """Dispatches an event to update the state."""
        with self.lock:
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

    def get_snapshot(self) -> RuntimeTruthState:
        """Returns the current state snapshot."""
        with self.lock:
            return self.state

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the state for API/Websocket export."""
        return asdict(self.get_snapshot())

# Global singleton
state_store = RuntimeStateStore()
