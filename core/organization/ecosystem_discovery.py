# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\organization\\ecosystem_discovery.py
"""Evidence-backed ecosystem discovery and reuse ranking.

Discovery inventories sources without importing or executing them. The engine ranks
candidates for capability acquisition and reports overlap signals so DGM-MAT can
reuse existing work without creating accidental runtime dependencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .capability_models import CapabilityCandidate, CapabilityRequest, CapabilitySource
from .source_discovery import LocalSourceDiscovery


@dataclass(slots=True)
class DiscoveryMatch:
    candidate: CapabilityCandidate
    reuse_score: float
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OverlapCluster:
    key: str
    source_ids: list[str]
    names: list[str]
    capabilities: list[str]


@dataclass(slots=True)
class DiscoveryReport:
    request_id: str
    matches: list[DiscoveryMatch]
    overlap_clusters: list[OverlapCluster]
    scanned_roots: list[str]


class EcosystemDiscovery:
    """Discover, rank and cluster reusable capability sources deterministically."""

    TRUST_BY_TYPE = {
        "local_project": 0.85,
        "dgm_lab": 0.80,
        "github_repository": 0.70,
        "installed_tool": 0.65,
        "external_skill": 0.40,
    }

    def __init__(self, roots: list[str | Path]) -> None:
        self.roots = [Path(r) for r in roots]

    def scan(self) -> list[CapabilitySource]:
        sources = LocalSourceDiscovery(self.roots).scan()
        for source in sources:
            source.source_type = self._classify_source(source.locator)
            source.trust = self.TRUST_BY_TYPE.get(source.source_type, source.trust)
        return sources

    def discover(
        self,
        request: CapabilityRequest,
        *,
        limit: int = 10,
    ) -> DiscoveryReport:
        sources = self.scan()
        matches: list[DiscoveryMatch] = []
        requested = self._terms(request)
        for source in sources:
            matched = sorted(
                term for term in requested
                if self._term_matches_source(term, source)
            )
            if not matched:
                continue

            fit = min(1.0, len(matched) / max(1, len(requested)))
            provenance = 0.08 if source.source_type in {"local_project", "dgm_lab"} else 0.18
            adaptation = self._adaptation_cost(source, matched)
            safety = max(0.0, min(1.0, source.trust - provenance))
            reuse_score = max(
                0.0,
                min(1.0, 0.55 * fit + 0.25 * safety + 0.20 * (1.0 - adaptation)),
            )
            notes = [
                f"matched skills: {', '.join(matched)}",
                f"source type: {source.source_type}",
                f"adaptation cost: {adaptation:.2f}",
            ]
            matches.append(
                DiscoveryMatch(
                    candidate=CapabilityCandidate(
                        candidate_id=f"candidate:{source.source_id}",
                        request_id=request.request_id,
                        source=source,
                        matched_skills=matched,
                        fit_score=fit,
                        safety_score=safety,
                        adaptation_cost=adaptation,
                        assessment_notes=notes,
                    ),
                    reuse_score=reuse_score,
                    reasons=notes,
                )
            )

        matches.sort(
            key=lambda item: (
                -item.reuse_score,
                item.candidate.adaptation_cost,
                item.candidate.source.name.lower(),
            )
        )
        return DiscoveryReport(
            request_id=request.request_id,
            matches=matches[:limit],
            overlap_clusters=self._clusters(sources),
            scanned_roots=[str(root) for root in self.roots],
        )

    def _terms(self, request: CapabilityRequest) -> set[str]:
        raw = [request.capability, *request.required_skills]
        terms: set[str] = set()
        for value in raw:
            terms.update(
                token for token in re.split(r"[^a-z0-9]+", value.lower())
                if len(token) >= 3
            )
        return terms

    @staticmethod
    def _term_matches_source(term: str, source: CapabilitySource) -> bool:
        haystack = " ".join(
            [source.name, *source.capabilities, *source.metadata.values()]
        ).lower()
        return term in haystack

    @staticmethod
    def _adaptation_cost(source: CapabilitySource, matched: list[str]) -> float:
        base = 0.20 if source.source_type == "dgm_lab" else 0.35
        if source.source_type == "local_project":
            base = 0.30
        if source.source_type == "external_skill":
            base = 0.75
        return max(0.0, min(1.0, base - min(0.15, 0.03 * len(matched))))

    @staticmethod
    def _classify_source(locator: str) -> str:
        normalized = locator.lower().replace("\\", "/")
        name = Path(locator).name.lower()
        if "lab" in name or "/labs/" in normalized:
            return "dgm_lab"
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return "external_skill"
        if "programs" in normalized or "programasgodmode" in normalized:
            return "local_project"
        return "local_project"

    @staticmethod
    def _clusters(sources: list[CapabilitySource]) -> list[OverlapCluster]:
        buckets: dict[str, list[CapabilitySource]] = {}
        for source in sources:
            caps = sorted(set(source.capabilities))
            if not caps:
                continue
            key = "+".join(caps)
            buckets.setdefault(key, []).append(source)

        clusters: list[OverlapCluster] = []
        for key, members in buckets.items():
            if len(members) < 2:
                continue
            clusters.append(
                OverlapCluster(
                    key=key,
                    source_ids=[member.source_id for member in members],
                    names=[member.name for member in members],
                    capabilities=key.split("+"),
                )
            )
        return sorted(clusters, key=lambda item: (-len(item.source_ids), item.key))
