from datetime import datetime, timedelta
from typing import Dict
from core.observability.logger import dgm_logger

class StormProtection:
    def __init__(self, threshold: int, window: int):
        self.threshold = threshold
        self.window = window
        self.counters: Dict[str, list[datetime]] = {} # source -> list of timestamps

    def check_storm(self, source: str) -> bool:
        """Returns True if a storm is detected from the given source."""
        now = datetime.now()
        if source not in self.counters:
            self.counters[source] = []

        self.counters[source] = [t for t in self.counters[source] if now - t < timedelta(seconds=self.window)]
        self.counters[source].append(now)

        if len(self.counters[source]) > self.threshold:
            dgm_logger.critical(f"StormProtection: STORM DETECTED from source {source}! ({len(self.counters[source])} events in {self.window}s)")
            return True

        return False
