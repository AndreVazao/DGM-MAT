import datetime
from typing import Dict, Any, List, Optional
from core.event_bus.bus import Event, EventBus

class EcosystemStateManager:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.repositories: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.provider_sessions: Dict[str, Dict[str, Any]] = {}
        self.memory_updates: List[Dict[str, Any]] = []
        self.evolution_chain: List[Dict[str, Any]] = []

        # Subscribe to ecosystem relevant events
        self.bus.subscribe("repo_update", self._handle_repo_update)
        self.bus.subscribe("agent_update", self._handle_agent_update)
        self.bus.subscribe("task_update", self._handle_task_update)
        self.bus.subscribe("provider_session", self._handle_provider_session)
        self.bus.subscribe("memory_sync", self._handle_memory_sync)
        self.bus.subscribe("system_repair", self._handle_evolution_event)
        self.bus.subscribe("deployment_update", self._handle_evolution_event)
        self.bus.subscribe("agent_upgraded", self._handle_evolution_event)
        self.bus.subscribe("*", self._handle_all_events)

    def _handle_repo_update(self, event: Event):
        repo_id = event.payload.get("repo_id")
        if repo_id:
            self.repositories[repo_id] = {
                "last_update": event.timestamp,
                "status": event.payload.get("status"),
                "metadata": event.payload.get("metadata", {})
            }

    def _handle_agent_update(self, event: Event):
        agent_id = event.payload.get("agent_id")
        if agent_id:
            self.agents[agent_id] = {
                "last_seen": event.timestamp,
                "status": event.payload.get("status"),
                "state": event.payload.get("state", {}),
                "type": event.payload.get("type")
            }

    def _handle_task_update(self, event: Event):
        task_id = event.payload.get("task_id")
        if task_id:
            self.tasks[task_id] = {
                "timestamp": event.timestamp,
                "status": event.payload.get("status"),
                "agent_id": event.payload.get("agent_id"),
                "trace_id": event.trace_id
            }

    def _handle_provider_session(self, event: Event):
        session_id = event.payload.get("session_id")
        if session_id:
            self.provider_sessions[session_id] = {
                "provider": event.payload.get("provider"),
                "status": event.payload.get("status"),
                "last_activity": event.timestamp
            }

    def _handle_memory_sync(self, event: Event):
        self.memory_updates.append({
            "timestamp": event.timestamp,
            "category": event.payload.get("category"),
            "version": event.payload.get("version"),
            "snapshot_id": event.payload.get("snapshot_id")
        })

    def _handle_evolution_event(self, event: Event):
        """Track mutations as evolution events."""
        evolution_record = {
            "timestamp": event.timestamp,
            "type": event.type,
            "source": event.source,
            "description": event.payload.get("description") or f"Evolution event triggered by {event.type}",
            "details": event.payload,
            "trace_id": event.trace_id,
            "is_evolution": True
        }
        self.evolution_chain.append(evolution_record)
        self._record_evolution(event)

    def _handle_all_events(self, event: Event):
        # Tracking evolution events for architecture/ecosystem changes
        if event.payload.get("is_evolution"):
            self._record_evolution(event)

    def _record_evolution(self, event: Event):
        """Task 7: Track ecosystem evolution over time."""
        evolution_record = {
            "timestamp": event.timestamp,
            "type": event.type,
            "description": event.payload.get("description") or f"System mutation: {event.type}",
            "changes": event.payload,
            "trace_id": event.trace_id
        }
        # Publish notification of recorded evolution
        self.bus.publish(Event(
            source="ecosystem_state",
            type="evolution_recorded",
            payload=evolution_record,
            priority="high"
        ))

    def get_global_state(self) -> Dict[str, Any]:
        return {
            "repositories": self.repositories,
            "agents": self.agents,
            "tasks": self.tasks,
            "provider_sessions": self.provider_sessions,
            "memory_updates": self.memory_updates[-10:], # Last 10 updates
            "evolution_chain_length": len(self.evolution_chain),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
