import time
import threading
from typing import List, Dict
from core.governance.governance_models import ResourceSnapshot
from core.observability.logger import dgm_logger

try:
    import psutil
except ImportError:
    psutil = None

class ResourceMonitor:
    def __init__(self, interval: int = 2):
        self.interval = interval
        self.running = False
        self.snapshot = None
        self.history: List[ResourceSnapshot] = []
        self.max_history = 300  # 10 minutes at 2s interval
        self._stop_event = threading.Event()
        self._lifecycle_lock = threading.Lock()
        self.thread = None

    def start(self, callback=None):
        """Start at most one monitor thread; repeated starts are idempotent."""
        with self._lifecycle_lock:
            if self.thread is not None and self.thread.is_alive():
                return
            self._stop_event.clear()
            self.running = True
            self.thread = threading.Thread(
                target=self._monitor_loop,
                args=(callback,),
                name="dgm-resource-monitor",
                daemon=True,
            )
            self.thread.start()

    def _monitor_loop(self, callback):
        while self.running and not self._stop_event.is_set():
            try:
                cpu = psutil.cpu_percent() if psutil else 0.0
                mem = psutil.virtual_memory().percent if psutil else 0.0

                # In a real system, these would come from relevant managers
                active_websockets = 0
                active_browsers = 0
                active_worktrees = 0

                self.snapshot = ResourceSnapshot(
                    cpu_percent=cpu,
                    memory_percent=mem,
                    event_queue_size=0,
                    active_websockets=active_websockets,
                    active_browsers=active_browsers,
                    active_worktrees=active_worktrees
                )

                self._analyze_trends(self.snapshot)

                if callback:
                    callback(self.snapshot)

            except Exception as exc:
                if not self._stop_event.is_set():
                    dgm_logger.error(f"ResourceMonitor: Failed to capture metrics: {exc}")

            if self._stop_event.wait(max(0.05, float(self.interval))):
                break

    def _analyze_trends(self, snapshot: ResourceSnapshot):
        """Hardening: Trend analysis (Requirement 6)."""
        self.history.append(snapshot)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        if len(self.history) < 10:
            return

        # 1. Sustained load detection
        recent_cpu = [s.cpu_percent for s in self.history[-10:]]
        avg_cpu = sum(recent_cpu) / len(recent_cpu)
        if avg_cpu > 90:
            dgm_logger.critical(f"ResourceMonitor: SUSTAINED HIGH CPU DETECTED ({avg_cpu:.1f}%)!")

        # 2. Memory leak suspicion (simple monotonic growth check)
        recent_mem = [s.memory_percent for s in self.history[-30:]]
        if all(recent_mem[i] <= recent_mem[i+1] for i in range(len(recent_mem)-1)) and recent_mem[-1] - recent_mem[0] > 5:
            dgm_logger.warning(f"ResourceMonitor: SUSPECTED MEMORY LEAK! (Growth: {recent_mem[0]:.1f}% -> {recent_mem[-1]:.1f}%)")

        # 3. Browser context explosion (Placeholder for actual count)
        if snapshot.active_browsers > 10:
            dgm_logger.warning(f"ResourceMonitor: BROWSER CONTEXT EXPLOSION DETECTED! ({snapshot.active_browsers})")

    def stop(self, timeout: float | None = None) -> bool:
        """Request shutdown and wait for the worker to exit cleanly."""
        with self._lifecycle_lock:
            self.running = False
            self._stop_event.set()
            thread = self.thread
        if thread is None or thread is threading.current_thread():
            return True
        wait_seconds = timeout if timeout is not None else max(1.0, float(self.interval) + 1.0)
        thread.join(timeout=max(0.0, wait_seconds))
        return not thread.is_alive()
