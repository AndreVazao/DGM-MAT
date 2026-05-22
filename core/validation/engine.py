import json
import hashlib
from typing import Any, Dict
from core.event_bus.bus import Event

class ValidationEngine:
    def __init__(self, event_schema_path: str):
        self.event_schema = self._load_schema(event_schema_path)
        self.critical_configs_hashes: Dict[str, str] = {}

    def _load_schema(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[VALIDATION ERROR] Failed to load schema: {e}")
            return {}

    def validate_event(self, event: Event) -> bool:
        """Minimal schema validation for the event."""
        # Check against schema structure (simplified for this task)
        event_dict = event.to_dict()
        schema_def = self.event_schema.get("event", {})

        for key in schema_def:
            if key not in event_dict:
                print(f"[VALIDATION ERROR] Event missing required key: {key}")
                return False

        # Priority check
        valid_priorities = ["low", "medium", "high", "critical"]
        if event.priority.lower() not in valid_priorities:
            print(f"[VALIDATION ERROR] Invalid priority: {event.priority}")
            return False

        return True

    def validate_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """Detect corrupted or invalid agent states."""
        if not agent_id or "status" not in state:
            return False
        return True

    def register_config_for_integrity(self, name: str, content: str):
        """Track hash of critical configurations."""
        self.critical_configs_hashes[name] = hashlib.sha256(content.encode()).hexdigest()

    def check_integrity(self, name: str, current_content: str) -> bool:
        """Verify hash of critical configurations."""
        if name not in self.critical_configs_hashes:
            return True
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()
        return current_hash == self.critical_configs_hashes[name]
