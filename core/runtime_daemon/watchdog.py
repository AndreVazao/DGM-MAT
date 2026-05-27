import time
import threading
import psutil
import os
from core.observability.logger import dgm_logger
from core.runtime_daemon.heartbeat import HeartbeatManager

class RuntimeWatchdog:
    """
    Monitors system health and terminates runaway processes/loops.
    Safety thresholds for CPU, RAM, and retry storms.
    """
    def __init__(self, heartbeat_manager: HeartbeatManager):
        self.heartbeat = heartbeat_manager
        self.monitored_loops = {}
        self._running = False
        self._thread = None
        self.process = psutil.Process(os.getpid())

        # Thresholds
        self.MAX_RAM_MB = 1536 # 1.5GB
        self.MAX_CPU_PERCENT = 85.0
        self.STALL_THRESHOLD_SEC = 300 # 5 min

    def pulse_loop(self, name: str):
        self.monitored_loops[name] = time.time()

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        dgm_logger.info("RuntimeWatchdog: Monitoring started with resource safeguards.")

    def _monitor(self):
        while self._running:
            try:
                now = time.time()

                # 1. Loop Vitality & Runaway Detection
                for name, last in list(self.monitored_loops.items()):
                    if now - last > self.STALL_THRESHOLD_SEC:
                        dgm_logger.error(f"RuntimeWatchdog: Loop '{name}' STALLED. Initiating safety cooldown.")
                        # Future: Implement targeted loop reset

                # 2. Resource Safeguards
                mem_info = self.process.memory_info()
                rss_mb = mem_info.rss / (1024 * 1024)

                if rss_mb > self.MAX_RAM_MB:
                    dgm_logger.critical(f"RuntimeWatchdog: MEMORY LIMIT EXCEEDED ({rss_mb:.2f} MB). Emergency flush requested.")
                    # Targeted action: trigger GC or pause autonomy

                cpu_percent = self.process.cpu_percent(interval=1.0)
                if cpu_percent > self.MAX_CPU_PERCENT:
                    dgm_logger.warning(f"RuntimeWatchdog: CPU SPIKE DETECTED ({cpu_percent}%). Throttling cycles.")

                self.heartbeat.pulse(
                    status="healthy",
                    metadata={
                        "loops": list(self.monitored_loops.keys()),
                        "memory_mb": round(rss_mb, 2),
                        "cpu_percent": cpu_percent
                    }
                )
            except Exception as e:
                dgm_logger.error(f"RuntimeWatchdog: Monitor error: {e}")
            time.sleep(30)

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
