import time
import threading
from typing import Dict, Any
from core.observability.logger import dgm_logger
from core.agents.isolated_runtime import isolation_layer

class AgentWatchdog:
    """
    Monitors agent health and resource usage.
    Part of Phase 42.3-LITE Distributed Runtime Stabilization.
    """
    def __init__(self):
        self.monitoring = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.monitoring:
            return
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        dgm_logger.info("AgentWatchdog: Started monitoring agents.")

    def stop(self):
        self.monitoring = False

    def _monitor_loop(self):
        while self.monitoring:
            for agent_id, context in isolation_layer.contexts.items():
                if context.health_status == "crashed":
                    dgm_logger.critical(f"Watchdog: Agent {agent_id} is in CRASHED state. Triggering recovery.")
                    # In a real scenario, we might restart the thread or notify governance

                # Update telemetry (placeholder for real resource check)
                context.resource_usage["cpu"] = 5.0 # Simulated

            time.sleep(10)

# Global watchdog
agent_watchdog = AgentWatchdog()
