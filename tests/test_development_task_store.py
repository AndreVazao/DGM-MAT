from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.development.task_result import DevelopmentTaskResult, TaskEvidence, TaskResultStatus
from core.development.task_store import (
    InvalidTaskTransitionError,
    TaskNotFoundError,
    TaskStore,
)


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "tasks.sqlite3"
        self.store = TaskStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_read_persisted_task(self):
        created = self.store.create(
            DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan only")
        )
        reopened = TaskStore(self.db_path).get("task-1")
        self.assertEqual(created.status, TaskResultStatus.PLANNED)
        self.assertEqual(reopened.summary, "Plan only")
        self.assertEqual(len(self.store.list_events("task-1")), 1)

    def test_duplicate_task_id_is_rejected(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        with self.assertRaises(InvalidTaskTransitionError):
            self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Again"))

    def test_new_task_must_start_planned(self):
        with self.assertRaises(InvalidTaskTransitionError):
            self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.RUNNING, "Running"))

    def test_happy_path_persists_history_and_verification_evidence(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        running = self.store.transition(
            "task-1", TaskResultStatus.RUNNING, "Worker started", expected_revision=1
        )
        self.assertEqual(running.status, TaskResultStatus.RUNNING)
        verified = self.store.transition(
            "task-1",
            TaskResultStatus.VERIFIED,
            "Tests and independent QA passed",
            evidence=(
                TaskEvidence("validation", "passed", "tests/result.txt"),
                TaskEvidence("independent_qa", "passed", "qa/review.txt"),
            ),
            validation_passed=True,
            independent_qa_passed=True,
            commit_sha="a" * 40,
            expected_revision=2,
        )
        reopened = TaskStore(self.db_path).get("task-1")
        self.assertEqual(reopened.status, TaskResultStatus.VERIFIED)
        self.assertTrue(reopened.validation_passed)
        self.assertTrue(reopened.independent_qa_passed)
        self.assertEqual(len(self.store.list_events("task-1")), 3)
        self.assertEqual(len(reopened.evidence), 2)

    def test_verified_transition_rejects_missing_evidence_atomically(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        self.store.transition("task-1", TaskResultStatus.RUNNING, "Running")
        with self.assertRaisesRegex(ValueError, "evidence references"):
            self.store.transition(
                "task-1", TaskResultStatus.VERIFIED, "Fake verified",
                validation_passed=True, independent_qa_passed=True,
            )
        after = self.store.get("task-1")
        self.assertEqual(after.status, TaskResultStatus.RUNNING)
        self.assertEqual(len(self.store.list_events("task-1")), 2)

    def test_failed_validation_evidence_cannot_be_marked_verified(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        self.store.transition("task-1", TaskResultStatus.RUNNING, "Running")
        with self.assertRaisesRegex(ValueError, "outcomes to be 'passed'"):
            self.store.transition(
                "task-1", TaskResultStatus.VERIFIED, "Claim false success",
                evidence=(
                    TaskEvidence("validation", "failed", "tests/result.txt"),
                    TaskEvidence("independent_qa", "passed", "qa/review.txt"),
                ),
                validation_passed=True, independent_qa_passed=True,
            )
        self.assertEqual(self.store.get("task-1").status, TaskResultStatus.RUNNING)

    def test_illegal_transition_is_rejected(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        with self.assertRaises(InvalidTaskTransitionError):
            self.store.transition("task-1", TaskResultStatus.VERIFIED, "Skip execution",
                evidence=(
                    TaskEvidence("validation", "passed", "tests/result.txt"),
                    TaskEvidence("independent_qa", "passed", "qa/review.txt"),
                ),
                validation_passed=True, independent_qa_passed=True)

    def test_stale_revision_is_rejected(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        self.store.transition("task-1", TaskResultStatus.RUNNING, "Running")
        with self.assertRaisesRegex(InvalidTaskTransitionError, "Stale task revision"):
            self.store.transition("task-1", TaskResultStatus.FAILED, "Failed", expected_revision=1)

    def test_missing_task_is_reported(self):
        with self.assertRaises(TaskNotFoundError):
            self.store.get("missing")

    def test_event_history_survives_reopen(self):
        self.store.create(DevelopmentTaskResult("task-1", TaskResultStatus.PLANNED, "Plan"))
        self.store.transition("task-1", TaskResultStatus.BLOCKED, "Awaiting approved tool")
        history = TaskStore(self.db_path).list_events("task-1")
        self.assertEqual([event["to_status"] for event in history], ["planned", "blocked"])


if __name__ == "__main__":
    unittest.main()
