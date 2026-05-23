from core.governance.governance_models import GovernanceState
from core.observability.logger import dgm_logger

class DegradationController:
    def __init__(self):
        self.state = GovernanceState()

    def update_degradation(self, cpu_usage: float, mem_usage: float, cpu_threshold: float, mem_threshold: float):
        if cpu_usage > cpu_threshold or mem_usage > mem_threshold:
            if not self.state.is_degraded:
                dgm_logger.warning(f"DegradationController: System ENTERING degraded mode (CPU: {cpu_usage}%, MEM: {mem_usage}%)")
                self.state.is_degraded = True
        else:
            if self.state.is_degraded:
                dgm_logger.info("DegradationController: System EXITING degraded mode. Back to normal operations.")
                self.state.is_degraded = False

    def is_degraded(self) -> bool:
        return self.state.is_degraded

    def should_throttle_low_priority(self) -> bool:
        return self.state.is_degraded or self.state.emergency_slowdown
