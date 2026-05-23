from typing import Dict, List
from datetime import datetime, timedelta
from shared.models.event import Event
from core.observability.logger import dgm_logger
from core.governance.runtime_limits import RuntimeLimits

class EventGovernor:
    def __init__(self, limits: RuntimeLimits):
        self.limits = limits
        self.event_history: List[datetime] = []

    def govern(self, event: Event) -> bool:
        """Returns True if the event is allowed, False otherwise."""
        # 1. Depth check
        if event.depth > self.limits.max_event_depth:
            dgm_logger.error(f"EventGovernor: Event depth exceeded {self.limits.max_event_depth}. Dropping event.")
            return False

        # 2. Rate check (Storm protection)
        now = datetime.now()
        self.event_history = [t for t in self.event_history if now - t < timedelta(seconds=self.limits.storm_time_window_seconds)]
        self.event_history.append(now)

        if len(self.event_history) > self.limits.storm_event_count_threshold:
            dgm_logger.critical(f"EventGovernor: EVENT STORM DETECTED! ({len(self.event_history)} events in {self.limits.storm_time_window_seconds}s)")
            return False

        return True
