import os
from typing import List, Set
from core.event_bus.bus import Event, EventBus

class DriftMonitor:
    def __init__(self, event_bus: EventBus, root_dir: str):
        self.bus = event_bus
        self.root_dir = root_dir
        self.expected_satellites = {
            "DGM-MAT-Mobile", "DGM-MAT-Plugins", "DGM-MAT-Labs",
            "DGM-MAT-Connectors", "DGM-MAT-Providers", "DGM-MAT-Assets", "DGM-MAT-Deploy"
        }

    def check_drift(self, active_agents: Set[str]):
        """Detect divergence between repo state, memory (agents), and expectations."""
        repo_satellites = self._get_repo_satellites()

        # 1. Missing modules/satellites
        missing = self.expected_satellites - repo_satellites
        if missing:
            self._emit_warning("drift_detected", f"Missing expected satellites: {missing}")

        # 2. Orphan agents (agents running without corresponding repo/config - simulated)
        # In this minimal version, we check if active agents have expected prefixes
        for agent in active_agents:
            if not any(agent.startswith(sat.replace("DGM-MAT-", "").lower()) for sat in self.expected_satellites) and agent != "overseer":
                self._emit_warning("orphan_agent", f"Agent {agent} does not match any known satellite prefix")

    def _get_repo_satellites(self) -> Set[str]:
        try:
            return {d for d in os.listdir(self.root_dir) if os.path.isdir(os.path.join(self.root_dir, d)) and d.startswith("DGM-MAT-")}
        except Exception:
            return set()

    def _emit_warning(self, type: str, message: str):
        self.bus.publish(Event(
            source="drift_monitor",
            type="error",
            payload={"message": message, "category": type},
            priority="high"
        ))
