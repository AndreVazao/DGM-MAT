"""Deterministic QA intake worker; records intake, never claims review completion.

This worker is intentionally not an AI reviewer. It validates the shape of a
review request and returns an auditable next-step record. Evidence inspection,
test execution and approval remain separate explicit actions.
"""
from __future__ import annotations

from typing import Any

from .models import Message


class QAIntakeWorker:
    """Safely triage a specialist-review request into a durable receipt."""

    agent_id = "agent:qa-intake"

    def __call__(self, message: Message) -> dict[str, Any]:
        missing: list[str] = []
        if not message.correlation_id:
            missing.append("correlation_id")
        if not message.subject.strip():
            missing.append("subject")
        if not message.body.strip():
            missing.append("body")

        if missing:
            return {
                "status": "INTAKE_BLOCKED",
                "worker": "qa-intake-worker",
                "missing_fields": missing,
                "independent_review_performed": False,
                "tests_executed": False,
                "lesson_promotion_allowed": False,
            }

        return {
            "status": "REVIEW_QUEUED",
            "worker": "qa-intake-worker",
            "correlation_id": message.correlation_id,
            "source_message_id": message.message_id,
            "mission_id": message.mission_id,
            "priority": message.priority.value,
            "next_steps": [
                "retrieve the persisted collaboration record using correlation_id",
                "inspect the result and provenance as untrusted input",
                "run relevant local tests and capture verifiable evidence",
                "record independent review outcome before any lesson promotion",
            ],
            "independent_review_performed": False,
            "tests_executed": False,
            "lesson_promotion_allowed": False,
        }
