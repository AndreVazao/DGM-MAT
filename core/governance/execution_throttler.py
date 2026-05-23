import time
from shared.enums.event_priority import EventPriority
from core.observability.logger import dgm_logger

class ExecutionThrottler:
    def __init__(self):
        self.throttled_until = {} # key -> timestamp

    def throttle(self, key: str, duration_seconds: int):
        self.throttled_until[key] = time.time() + duration_seconds
        dgm_logger.info(f"ExecutionThrottler: Throttling {key} for {duration_seconds}s")

    def is_throttled(self, key: str) -> bool:
        if key in self.throttled_until:
            if time.time() < self.throttled_until[key]:
                return True
            else:
                del self.throttled_until[key]
        return False

    def get_delay(self, priority: EventPriority) -> float:
        if priority == EventPriority.LOW:
            return 0.5
        elif priority == EventPriority.MEDIUM:
            return 0.2
        return 0.0
