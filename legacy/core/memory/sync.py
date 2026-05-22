import os
import shutil
import json
import datetime
from typing import List, Dict, Any
from core.event_bus.bus import Event, EventBus

class MemorySync:
    def __init__(self, event_bus: EventBus, core_memory_path: str = "core/memory/storage", andreos_path: str = "AndreOS"):
        self.bus = event_bus
        self.core_memory_path = core_memory_path
        self.andreos_path = andreos_path
        os.makedirs(self.andreos_path, exist_ok=True)
        os.makedirs(os.path.join(self.core_memory_path, "snapshots"), exist_ok=True)

        # Subscribe to evolution recorded events
        self.bus.subscribe("evolution_recorded", self._handle_evolution_sync)

    def _handle_evolution_sync(self, event: Event):
        """Task 7: Handle state snapshots for evolution events."""
        snapshot_id = f"evolution_{event.trace_id[:8]}"
        self.save_evolution_snapshot(snapshot_id, event.payload)

    def save_evolution_snapshot(self, snapshot_id: str, data: Dict[str, Any]):
        filename = f"evolution_{snapshot_id}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        filepath = os.path.join(self.core_memory_path, "snapshots", filename)

        payload = {
            "snapshot_id": snapshot_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "data": data
        }

        with open(filepath, 'w') as f:
            json.dump(payload, f, indent=2)

        # Sync to AndreOS immediately for evolution events
        self.sync_to_andreos()

    def sync_to_andreos(self) -> List[str]:
        """Sync all snapshots from core memory to AndreOS (Long-Term Memory)."""
        snapshots_src = os.path.join(self.core_memory_path, "snapshots")
        if not os.path.exists(snapshots_src):
            return []

        synced_files = []
        for filename in os.listdir(snapshots_src):
            src_file = os.path.join(snapshots_src, filename)
            dest_file = os.path.join(self.andreos_path, filename)

            # Append-only: copy if it doesn't exist in destination
            if not os.path.exists(dest_file):
                shutil.copy2(src_file, dest_file)
                synced_files.append(filename)

        if synced_files:
            self.bus.publish(Event(
                source="memory_sync",
                type="memory_sync_completed",
                payload={"files": synced_files},
                priority="low"
            ))

        return synced_files

    def check_consistency(self) -> bool:
        """Verify that all core snapshots are present in AndreOS."""
        snapshots_src = os.path.join(self.core_memory_path, "snapshots")
        if not os.path.exists(snapshots_src):
            return True

        for filename in os.listdir(snapshots_src):
            dest_file = os.path.join(self.andreos_path, filename)
            if not os.path.exists(dest_file):
                return False
        return True
