# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\organization\\help_seeking.py
"""Governed help-seeking and zero-cost-by-default decisions.

This module is a deterministic policy primitive. It does not call providers,
spend credits, send messages, or execute tasks. Integrators must honor its
decision before invoking any external capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class HelpAction(str, Enum):
    PROCEED = "PROCEED"
    INVESTIGATE_FREE = "INVESTIGATE_FREE"
    DELEGATE_SPECIALIST = "DELEGATE_SPECIALIST"
    ASK_USER = "ASK_USER"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class HelpContext:
    goal: str
    known_facts: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    attempted_steps: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    free_options: tuple[str, ...] = ()
    specialist_available: bool = False
    user_decision_required: bool = False
    paid_option_only: bool = False
    paid_option_description: str = ""
    explicit_spending_approval: bool = False
    max_attempts_reached: bool = False


@dataclass(frozen=True, slots=True)
class HelpDecision:
    action: HelpAction
    reason: str
    next_step: str
    spending_allowed: bool = False
    help_request: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


class HelpSeekingPolicy:
    """Select the safest next step without assuming knowledge or budget."""

    @staticmethod
    def decide(context: HelpContext) -> HelpDecision:
        goal = context.goal.strip() if isinstance(context.goal, str) else ""
        if not goal:
            return HelpDecision(
                HelpAction.ASK_USER,
                "The mission goal is missing or invalid.",
                "Ask the user to state the desired outcome.",
                help_request="What result do you want me to achieve?",
            )

        if context.explicit_spending_approval:
            return HelpDecision(
                HelpAction.BLOCKED,
                "Spending approval alone is not a provider/tool authorization or cost validation.",
                "Verify the exact provider, amount/limit, quota and operation through the governed execution layer.",
                spending_allowed=False,
                help_request=HelpSeekingPolicy.build_request(context, "Validate the exact cost and approved operation."),
            )

        if context.user_decision_required:
            return HelpDecision(
                HelpAction.ASK_USER,
                "A material decision or authorization belongs to the user.",
                "Ask one focused question and include the available options and consequences.",
                help_request=HelpSeekingPolicy.build_request(context, "Request the specific user decision/authorization."),
            )

        if context.max_attempts_reached:
            return HelpDecision(
                HelpAction.BLOCKED,
                "The bounded attempt budget has been reached; do not loop or retry blindly.",
                "Preserve evidence, mark the task BLOCKED/PARTIAL, and route a concrete help request.",
                help_request=HelpSeekingPolicy.build_request(context, "Investigate the blocker and recommend the next safe step."),
            )

        if context.specialist_available:
            return HelpDecision(
                HelpAction.DELEGATE_SPECIALIST,
                "A suitable internal specialist is available; use internal help before external spending.",
                "Delegate with goal, facts, attempts, evidence, constraints and a specific question.",
                help_request=HelpSeekingPolicy.build_request(context, "Resolve the specialist-level unknown or blocker."),
            )

        free_options = tuple(
            option.strip() for option in context.free_options
            if isinstance(option, str) and option.strip()
        )
        if free_options:
            return HelpDecision(
                HelpAction.INVESTIGATE_FREE,
                "At least one potentially free/local option is available.",
                "Try the first safe free option and record the evidence before escalating.",
                help_request=HelpSeekingPolicy.build_request(context, "Investigate using a free/local option."),
                metadata={"free_options": free_options},
            )

        if context.paid_option_only:
            request = HelpSeekingPolicy.build_request(
                context,
                "No verified safe/free route is available. Ask whether to authorize the exact paid option; do not execute it yet.",
            )
            return HelpDecision(
                HelpAction.BLOCKED,
                "Only a potentially paid option is known and no explicit cost-specific authorization has been validated.",
                "Stop before consuming credits or money; report the exact cost/limit needed for an informed decision.",
                spending_allowed=False,
                help_request=request,
            )

        if context.unknowns:
            return HelpDecision(
                HelpAction.INVESTIGATE_FREE,
                "There are unresolved unknowns; gather evidence from existing local resources and documentation first.",
                "Inspect existing memory, code, tests and official documentation without making external paid calls.",
                help_request=HelpSeekingPolicy.build_request(context, "Find reliable evidence for the unresolved unknowns."),
            )

        return HelpDecision(
            HelpAction.PROCEED,
            "No explicit blocker or unresolved unknown was supplied.",
            "Proceed within the task's existing permissions and verify the result before claiming success.",
        )

    @staticmethod
    def build_request(context: HelpContext, specific_ask: str) -> str:
        """Build an actionable, evidence-led request without fabricating context."""
        sections: list[str] = [f"Goal: {context.goal.strip() or 'Not provided'}"]
        if context.known_facts:
            sections.append("Verified facts: " + "; ".join(context.known_facts))
        if context.unknowns:
            sections.append("Unknowns: " + "; ".join(context.unknowns))
        if context.attempted_steps:
            sections.append("Attempts already made: " + "; ".join(context.attempted_steps))
        if context.evidence:
            sections.append("Evidence: " + "; ".join(context.evidence))
        if context.free_options:
            sections.append("Known free/local options: " + "; ".join(context.free_options))
        if context.paid_option_description:
            sections.append("Potential paid option (not authorized): " + context.paid_option_description)
        sections.append("Specific help requested: " + specific_ask.strip())
        return "\n".join(sections)

    @staticmethod
    def may_spend(*, explicit_approval: bool, cost_known: bool, within_approved_limit: bool) -> bool:
        """Fail-closed gate; all three independent conditions must be true."""
        return (
            type(explicit_approval) is bool and explicit_approval
            and type(cost_known) is bool and cost_known
            and type(within_approved_limit) is bool and within_approved_limit
        )
