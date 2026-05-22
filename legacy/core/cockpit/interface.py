import datetime
from typing import Dict, List, Any, Optional
from core.event_bus.bus import Event, EventBus

class CockpitInterface:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.event_stream: List[Dict[str, Any]] = []
        self.agent_health: Dict[str, str] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.system_status = "nominal"

        # Subscribe to all events for the stream
        self.bus.subscribe("*", self._on_event)
        self.bus.subscribe("agent_update", self._on_agent_update)
        self.bus.subscribe("approval_request", self._on_approval_request)

    def _on_event(self, event: Event):
        self.event_stream.append(event.to_dict())
        if len(self.event_stream) > 100:
            self.event_stream.pop(0)

    def _on_agent_update(self, event: Event):
        agent_id = event.payload.get("agent_id")
        if agent_id:
            self.agent_health[agent_id] = event.payload.get("status", "unknown")

    def _on_approval_request(self, event: Event):
        approval_id = event.id
        self.pending_approvals[approval_id] = {
            "type": event.payload.get("request_type"),
            "description": event.payload.get("description"),
            "context": event.payload.get("context"),
            "timestamp": event.timestamp
        }

    def get_dashboard_state(self) -> Dict[str, Any]:
        return {
            "system_status": self.system_status,
            "agent_health": self.agent_health,
            "event_stream_tail": self.event_stream[-10:],
            "pending_approvals_count": len(self.pending_approvals),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def process_approval(self, approval_id: str, decision: bool):
        """Manual intervention: approve or reject a pending request."""
        if approval_id in self.pending_approvals:
            request = self.pending_approvals.pop(approval_id)
            self.bus.publish(Event(
                source="cockpit",
                type="approval_response",
                payload={
                    "approval_id": approval_id,
                    "approved": decision,
                    "request_type": request["type"]
                },
                priority="high"
            ))
            return True
        return False

    def send_manual_command(self, target: str, command: str, payload: Dict[str, Any] = None):
        """Inject a manual command into the event bus."""
        self.bus.publish(Event(
            source="cockpit_manual",
            target=target,
            type="task",
            payload={"task_type": "manual_intervention", "command": command, "data": payload or {}},
            priority="high"
        ))
