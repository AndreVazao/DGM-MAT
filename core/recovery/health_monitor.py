import time
from datetime import datetime
from typing import Dict, Any, Callable
from threading import Thread
from core.recovery.recovery_models import HealthStatus
from core.observability.logger import dgm_logger

class HealthMonitor:
    def __init__(self, interval: int = 3):
        self.interval = interval
        self.monitors: Dict[str, Callable[[], HealthStatus]] = {}
        self.health_history: Dict[str, HealthStatus] = {}
        self.running = False

    def add_monitor(self, name: str, check_fn: Callable[[], HealthStatus]):
        self.monitors[name] = check_fn

    def start(self):
        self.running = True
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            for name, check_fn in self.monitors.items():
                try:
                    status = check_fn()
                    self.health_history[name] = status
                    if not status.is_healthy:
                        dgm_logger.warning(f"Health Monitor: {name} is unhealthy!")
                except Exception as exc:
                    dgm_logger.error(f"Health Monitor error for {name}: {exc}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False
