from core.observability.logger import dgm_logger

class DegradationManager:
    def __init__(self):
        self.degraded_mode = False

    def enter_degraded_mode(self, reason: str):
        dgm_logger.warning(f"Entering degraded mode. Reason: {reason}")
        self.degraded_mode = True

    def exit_degraded_mode(self):
        dgm_logger.info("Exiting degraded mode. System health restored.")
        self.degraded_mode = False
