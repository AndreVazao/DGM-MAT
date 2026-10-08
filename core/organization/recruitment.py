"""Open recruitment and capability acquisition orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from .capability_models import (
    CapabilityCandidate,
    CapabilityRequest,
    RecruitmentOrder,
    RecruitmentStatus,
)
from .capability_registry import CapabilityRegistry
from .registry import AgentRegistry


@dataclass(slots=True)
class RecruitmentDecision:
    order: RecruitmentOrder
    rationale: str


class RecruitmentEngine:
    """Lets HQ request new workers/capabilities without hard-coding a fixed fleet.

    Low-risk internal capability reuse can proceed through the normal governed
    pipeline. External, credentialed, destructive or high-risk acquisition is
    marked for human approval.
    """

    HIGH_RISK = {"high", "critical", "external_credentials", "destructive"}

    def __init__(self, capabilities: CapabilityRegistry, agents: AgentRegistry) -> None:
        self.capabilities = capabilities
        self.agents = agents

    def propose_hire(
        self,
        request: CapabilityRequest,
        candidate: CapabilityCandidate,
        *,
        role: str,
        department_id: str,
    ) -> RecruitmentDecision:
        if self.capabilities.get_request(request.request_id) is None:
            self.capabilities.request(request)
        if self.capabilities.get_candidate(candidate.candidate_id) is None:
            self.capabilities.add_candidate(candidate)

        needs_approval = (
            request.risk_level in self.HIGH_RISK
            or candidate.source.source_type == "external"
            or not candidate.provenance_required
        )
        order = RecruitmentOrder(
            request_id=request.request_id,
            candidate_id=candidate.candidate_id,
            role=role,
            department_id=department_id,
            status=(
                RecruitmentStatus.APPROVAL_REQUIRED
                if needs_approval
                else RecruitmentStatus.APPROVED
            ),
            approval_required=needs_approval,
            approval_reason=(
                "Human approval required for high-risk/external/unproven capability."
                if needs_approval
                else None
            ),
        )
        return RecruitmentDecision(
            order=order,
            rationale=(
                "Capability can enter the governed forge."
                if not needs_approval
                else "Capability must stop at the approval gate."
            ),
        )
