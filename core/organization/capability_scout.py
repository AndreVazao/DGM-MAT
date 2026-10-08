# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\organization\\capability_scout.py
"""Governed Capability Scout worker facade.

The scout discovers and ranks reusable sources but never promotes or executes them.
"""

from __future__ import annotations

from pathlib import Path

from .capability_models import CapabilityRequest
from .ecosystem_discovery import EcosystemDiscovery


class CapabilityScout:
    agent_id = "agent:capability-scout"

    def __init__(self, roots: list[str | Path] | None = None) -> None:
        roots = roots or [
            Path("C:/ProgramasGodMode"),
            Path("C:/DevopGodMode"),
        ]
        self.discovery = EcosystemDiscovery(roots)

    def discover(
        self,
        capability: str,
        reason: str,
        mission_id: str = "mission:capability-scout",
        required_skills: list[str] | None = None,
    ) -> dict:
        request = CapabilityRequest(
            request_id=f"capability:{capability.strip().lower().replace(' ', '-')}",
            capability=capability,
            reason=reason,
            mission_id=mission_id,
            requested_by=self.agent_id,
            required_skills=required_skills or [],
        )
        report = self.discovery.discover(request)
        return {
            "schema": "dgm-mat.capability-scout.v1",
            "agent_id": self.agent_id,
            "request": {
                "request_id": request.request_id,
                "capability": request.capability,
                "reason": request.reason,
                "required_skills": request.required_skills,
            },
            "matches": [
                {
                    "candidate_id": item.candidate.candidate_id,
                    "name": item.candidate.source.name,
                    "source_type": item.candidate.source.source_type,
                    "locator": item.candidate.source.locator,
                    "matched_skills": item.candidate.matched_skills,
                    "fit_score": item.candidate.fit_score,
                    "safety_score": item.candidate.safety_score,
                    "adaptation_cost": item.candidate.adaptation_cost,
                    "reuse_score": item.reuse_score,
                    "reasons": item.reasons,
                }
                for item in report.matches
            ],
            "overlap_clusters": [
                {
                    "key": cluster.key,
                    "source_ids": cluster.source_ids,
                    "names": cluster.names,
                    "capabilities": cluster.capabilities,
                }
                for cluster in report.overlap_clusters
            ],
            "scanned_roots": report.scanned_roots,
            "promotion": "not_performed",
            "execution": "not_performed",
        }
