from __future__ import annotations

import unittest

from core.development.task_result import (
    DevelopmentTaskResult,
    TaskEvidence,
    TaskResultStatus,
)


class DevelopmentTaskResultTests(unittest.TestCase):
    def test_planned_result_does_not_claim_execution(self):
        result = DevelopmentTaskResult(
            task_id="task-1",
            status=TaskResultStatus.PLANNED,
            summary="Plan prepared; no source changes made.",
        )
        self.assertEqual(result.to_dict()["status"], "planned")
        self.assertFalse(result.to_dict()["validation_passed"])
        self.assertFalse(result.to_dict()["independent_qa_passed"])

    def test_empty_task_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "task_id"):
            DevelopmentTaskResult("", TaskResultStatus.PLANNED, "Plan only")

    def test_empty_summary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "summary"):
            DevelopmentTaskResult("task-1", TaskResultStatus.BLOCKED, " ")

    def test_verified_requires_validation_pass(self):
        with self.assertRaisesRegex(ValueError, "validation_passed"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.VERIFIED, "Verified",
                evidence=(
                    TaskEvidence("validation", "passed", "test://validation"),
                    TaskEvidence("independent_qa", "passed", "test://qa"),
                ),
                independent_qa_passed=True,
            )

    def test_verified_requires_independent_qa_pass(self):
        with self.assertRaisesRegex(ValueError, "independent_qa_passed"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.VERIFIED, "Verified",
                evidence=(
                    TaskEvidence("validation", "passed", "test://validation"),
                    TaskEvidence("independent_qa", "passed", "test://qa"),
                ),
                validation_passed=True,
            )

    def test_verified_rejects_duplicate_failed_evidence(self):
        with self.assertRaisesRegex(ValueError, "all validation and independent QA"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.VERIFIED, "Verified",
                evidence=(
                    TaskEvidence("validation", "passed", "test://validation-1"),
                    TaskEvidence("validation", "failed", "test://validation-2"),
                    TaskEvidence("independent_qa", "passed", "test://qa"),
                ),
                validation_passed=True,
                independent_qa_passed=True,
            )

    def test_verified_requires_both_evidence_types(self):
        with self.assertRaisesRegex(ValueError, "evidence references"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.VERIFIED, "Verified",
                evidence=(TaskEvidence("validation", "passed", "test://validation"),),
                validation_passed=True,
                independent_qa_passed=True,
            )

    def test_evidence_requires_nonempty_reference(self):
        with self.assertRaisesRegex(ValueError, "must be non-empty"):
            TaskEvidence("independent_qa", "passed", " ")

    def test_verified_rejects_failed_evidence_even_when_flags_are_true(self):
        with self.assertRaisesRegex(ValueError, "outcomes to be 'passed'"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.VERIFIED, "Verified",
                evidence=(
                    TaskEvidence("validation", "failed", "test://validation"),
                    TaskEvidence("independent_qa", "passed", "test://qa"),
                ),
                validation_passed=True,
                independent_qa_passed=True,
            )

    def test_non_verified_result_cannot_claim_pass_flags(self):
        with self.assertRaisesRegex(ValueError, "only be set"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.RUNNING, "Still running",
                validation_passed=True,
            )

    def test_commit_hash_must_be_full_hex(self):
        with self.assertRaisesRegex(ValueError, "full 40- or 64-character"):
            DevelopmentTaskResult(
                "task-1", TaskResultStatus.FAILED, "Patch failed", commit_sha="deadbeef"
            )

    def test_verified_result_serializes_evidence_without_claim_inference(self):
        result = DevelopmentTaskResult(
            "task-1",
            TaskResultStatus.VERIFIED,
            "Tests and independent review passed.",
            evidence=(
                TaskEvidence("validation", "passed", "tests/summary.json"),
                TaskEvidence("independent_qa", "passed", "qa/review-17"),
            ),
            validation_passed=True,
            independent_qa_passed=True,
            commit_sha="a" * 40,
        )
        payload = result.to_dict()
        self.assertEqual(payload["status"], "verified")
        self.assertEqual(len(payload["evidence"]), 2)
        self.assertEqual(payload["commit_sha"], "a" * 40)


if __name__ == "__main__":
    unittest.main()
