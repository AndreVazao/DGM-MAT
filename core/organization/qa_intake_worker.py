"""Deterministic QA intake worker; records intake, never claims review completion.

This worker is intentionally not an AI reviewer. It validates the shape of a
review request and returns an auditable next-step record. Evidence inspection,
test execution and approval remain separate explicit actions.
"""
from __future__ import annotations

from typing import Any

from .models import Message
from .qa_review_queue import QAReviewQueue


class QAIntakeWorker:
    """Safely triage a specialist-review request into a durable receipt."""

    agent_id = "agent:qa-intake"

    def __init__(self, review_queue: QAReviewQueue | None = None) -> None:
        self.review_queue = review_queue

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

        work_item = None
        if self.review_queue is not None:
            work_item = self.review_queue.enqueue(
                correlation_id=message.correlation_id,
                source_message_id=message.message_id,
                mission_id=message.mission_id,
                subject=message.subject,
                request_body=message.body,
                priority=message.priority.value,
            )

        return {
            "status": "REVIEW_QUEUED",
            "worker": "qa-intake-worker",
            "work_item": work_item,
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
