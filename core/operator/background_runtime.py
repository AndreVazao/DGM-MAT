import time
from core.operator.autonomous_operator import AutonomousOperator
from core.observability.logger import dgm_logger

class BackgroundRuntime:
    """
    Continuous background runtime for DGM-MAT.
    """
    def __init__(self, interval: int = 300):
        self.operator = AutonomousOperator()
        self.interval = interval
        self._active = False

    def run(self):
        self._active = True
        self.operator.start()
        try:
            while self._active:
                self.operator.run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._active = False
        self.operator.stop()
