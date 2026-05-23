import time
from typing import Dict
from core.observability.logger import dgm_logger

class ProviderRateControl:
    def __init__(self, max_requests: int):
        self.max_requests = max_requests
        self.request_counts: Dict[str, list[float]] = {} # provider -> timestamps

    def allow_request(self, provider_id: str) -> bool:
        now = time.time()
        if provider_id not in self.request_counts:
            self.request_counts[provider_id] = []

        # Keep only last 60 seconds
        self.request_counts[provider_id] = [t for t in self.request_counts[provider_id] if now - t < 60]

        if len(self.request_counts[provider_id]) >= self.max_requests:
            dgm_logger.warning(f"ProviderRateControl: Rate limit exceeded for provider {provider_id} ({self.max_requests} req/min)")
            return False

        self.request_counts[provider_id].append(now)
        return True
