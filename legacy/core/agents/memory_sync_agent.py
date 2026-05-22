from typing import Any
from core.agents.base import BaseAgent
from core.event_bus.bus import Event, EventBus
from core.memory.engine import MemoryEngine
from core.memory.sync import MemorySync

class MemorySyncAgent(BaseAgent):
    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, "memory_sync", event_bus)
        self.engine = MemoryEngine()
        self.syncer = MemorySync()
        self.bus.subscribe("memory_snapshot_request", self._handle_snapshot_request)

    def _handle_snapshot_request(self, event: Event):
        category = event.payload.get("category", "general")
        data = event.payload.get("data", {})
        filepath = self.engine.save_snapshot(category, data)
        self._log(f"Snapshot saved to {filepath}")

        # Trigger sync to AndreOS
        self.syncer.sync_to_andreos()

        # Publish completion
        self.bus.publish(Event(
            source=self.id,
            type="memory_sync",
            payload={
                "category": category,
                "snapshot_id": filepath,
                "status": "synced"
            }
        ))

    def execute_logic(self, task: Event) -> Any:
        if task.payload.get("task_type") == "full_sync":
            files = self.syncer.sync_to_andreos()
            return f"Synced {len(files)} files to AndreOS"
        return "Memory sync logic executed"
