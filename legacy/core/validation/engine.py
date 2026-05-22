import json
import hashlib
from typing import Any, Dict, List
from core.event_bus.bus import Event

class ValidationEngine:
    def __init__(self, event_schema_path: str = "schemas/event.schema.json"):
        self.event_schema = self._load_schema(event_schema_path)
        self.critical_configs_hashes: Dict[str, str] = {}

    def _load_schema(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            # Fallback schema if file not found
            return {
                "event": ["id", "source", "type", "payload", "priority", "timestamp"]
            }

    def validate_event(self, event: Event) -> bool:
        """Schema and integrity validation for the event."""
        event_dict = event.to_dict()
        required_keys = self.event_schema.get("event", [])

        for key in required_keys:
            if key not in event_dict:
                print(f"[VALIDATION ERROR] Event missing required key: {key}")
                return False

        # Priority check
        valid_priorities = ["low", "medium", "high", "critical"]
        if event.priority.lower() not in valid_priorities:
            print(f"[VALIDATION ERROR] Invalid priority: {event.priority}")
            return False

        return True

    def validate_memory_consistency(self, core_snapshots: List[str], andreos_snapshots: List[str]) -> bool:
        """Task 6: Ensure AndreOS vs DGM-MAT alignment."""
        # Simplified: all core snapshots must be in AndreOS
        for snap in core_snapshots:
            if snap not in andreos_snapshots:
                return False
        return True

    def validate_agent_behavior(self, agent_id: str, action: str, allowed_actions: List[str]) -> bool:
        """Task 6: Prevent unauthorized actions."""
        return action in allowed_actions

    def validate_repo_state(self, current_repos: List[str], expected_repos: List[str]) -> bool:
        """Task 6: Detect desync between repos and ecosystem graph."""
        return set(current_repos) == set(expected_repos)
