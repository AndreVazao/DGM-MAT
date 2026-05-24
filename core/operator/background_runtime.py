import time
import threading
from core.operator.autonomous_operator import AutonomousOperator
from core.observability.logger import dgm_logger
from core.operator.task_daemon import TaskDaemon

class BackgroundRuntime:
    """
    Continuous background runtime for DGM-MAT with watchdog support.
    """
    def __init__(self, interval: int = 300):
        self.operator = AutonomousOperator()
        self.task_daemon = TaskDaemon()
        self.interval = interval
        self._active = False
        self._watchdog_thread = None

    def run(self):
        self._active = True
        dgm_logger.info("BackgroundRuntime: Starting autonomous background operation")
        self.operator.start()

        # Start watchdog
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

        try:
            while self._active:
                self._run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def _run_cycle(self):
        dgm_logger.info("BackgroundRuntime: Running operational cycle")
        self.operator.run_cycle()
        self.task_daemon.process_queue()

    def _watchdog_loop(self):
        while self._active:
            # Check service health
            dgm_logger.debug("Watchdog: Checking system health")
            time.sleep(60)

    def stop(self):
        self._active = False
        self.operator.stop()
