# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\governance\\provider_rate_control.py

import threading
import time
from typing import Dict, List

from core.observability.logger import dgm_logger


class ProviderRateControl:
    """Thread-safe, process-local sliding-window limiter for provider IDs."""

    WINDOW_SECONDS = 60.0

    def __init__(self, max_requests: int):
        if isinstance(max_requests, bool) or not isinstance(max_requests, int) or max_requests < 1:
            raise ValueError("max_requests must be a positive integer")
        self.max_requests = max_requests
        self.request_counts: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def allow_request(self, provider_id: str) -> bool:
        """Reserve one request slot; malformed IDs and limits fail closed."""
        if not isinstance(provider_id, str) or not provider_id.strip():
            return False
        provider_id = provider_id.strip()
        now = time.monotonic()

        with self._lock:
            timestamps = self.request_counts.get(provider_id, [])
            cutoff = now - self.WINDOW_SECONDS
            timestamps = [timestamp for timestamp in timestamps if timestamp > cutoff]

            if len(timestamps) >= self.max_requests:
                self.request_counts[provider_id] = timestamps
                dgm_logger.warning(
                    "ProviderRateControl: Rate limit exceeded for provider "
                    f"{provider_id} ({self.max_requests} req/min)"
                )
                return False

            timestamps.append(now)
            self.request_counts[provider_id] = timestamps
            return True
