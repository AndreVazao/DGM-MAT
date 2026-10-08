"""Runtime registry for acquired capabilities and promoted modules."""

from __future__ import annotations

from threading import RLock

from .capability_models import CapabilityCandidate, CapabilityRequest


class CapabilityRegistry:
    def __init__(self) -> None:
        self._requests: dict[str, CapabilityRequest] = {}
        self._candidates: dict[str, CapabilityCandidate] = {}
        self._lock = RLock()

    def request(self, request: CapabilityRequest) -> CapabilityRequest:
        with self._lock:
            if request.request_id in self._requests:
                raise ValueError(f"Capability request already exists: {request.request_id}")
            self._requests[request.request_id] = request
            return request

    def add_candidate(self, candidate: CapabilityCandidate) -> CapabilityCandidate:
        with self._lock:
            if candidate.candidate_id in self._candidates:
                raise ValueError(f"Capability candidate already exists: {candidate.candidate_id}")
            if candidate.request_id not in self._requests:
                raise ValueError(f"Unknown capability request: {candidate.request_id}")
            self._candidates[candidate.candidate_id] = candidate
            return candidate

    def get_request(self, request_id: str) -> CapabilityRequest | None:
        with self._lock:
            return self._requests.get(request_id)

    def get_candidate(self, candidate_id: str) -> CapabilityCandidate | None:
        with self._lock:
            return self._candidates.get(candidate_id)

    def candidates_for(self, request_id: str) -> list[CapabilityCandidate]:
        with self._lock:
            return [c for c in self._candidates.values() if c.request_id == request_id]
