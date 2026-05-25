import time
import threading
from core.observability.logger import dgm_logger
from core.runtime_daemon.heartbeat import HeartbeatManager

class RuntimeWatchdog:
    def __init__(self, heartbeat_manager: HeartbeatManager):
        self.heartbeat = heartbeat_manager
        self.monitored_loops = {}
        self._running = False
        self._thread = None

    def pulse_loop(self, name: str):
        self.monitored_loops[name] = time.time()

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        dgm_logger.info("RuntimeWatchdog: Monitoring started.")

    def _monitor(self):
        while self._running:
            try:
                now = time.time()
                for name, last in list(self.monitored_loops.items()):
                    if now - last > 300: # 5 min
                        dgm_logger.error(f"RuntimeWatchdog: Loop '{name}' STALLED")
                self.heartbeat.pulse(status="healthy", metadata={"loops": list(self.monitored_loops.keys())})
            except Exception as e:
                dgm_logger.error(f"RuntimeWatchdog: Monitor error: {e}")
            time.sleep(30)

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
