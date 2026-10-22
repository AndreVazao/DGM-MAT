from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from core.development.evidence_envelope import (
    EvidenceEnvelope,
    EvidenceExpectation,
    EvidenceVerificationError,
    verify_evidence,
)


BASE = "a" * 40
SOURCE = "b" * 40
QA_SOURCE = "c" * 40
TRUST = {
    "validator-service": ("validation",),
    "qa-service": ("independent_qa",),
}


class EvidenceEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "reports").mkdir()
        self.artifact = self.root / "reports" / "result.txt"
        self.artifact.write_text("tests passed\n", encoding="utf-8")
        self.expected = EvidenceExpectation(
            task_id="task-1",
            run_id="run-1",
            repo_root=str(self.root),
            source_commit_sha=SOURCE,
            allowed_paths=("reports",),
        )

    def envelope(self, **overrides):
        values = dict(
            task_id="task-1",
            run_id="run-1",
            repo_root=str(self.root),
            base_commit_sha=BASE,
            source_commit_sha=SOURCE,
            kind="validation",
            command_id="pytest-focused",
            exit_code=0,
            artifact_path="reports/result.txt",
            artifact_sha256=hashlib.sha256(self.artifact.read_bytes()).hexdigest(),
            producer_id="validator-service",
            producer_role="validator",
        )
        values.update(overrides)
        return EvidenceEnvelope(**values)

    def test_valid_evidence_returns_resolved_artifact(self):
        self.assertEqual(
            verify_evidence(self.envelope(), self.expected, trusted_producers=TRUST),
            self.artifact,
        )

    def test_missing_artifact_is_rejected(self):
        envelope = self.envelope(artifact_path="reports/missing.txt")
        with self.assertRaises((FileNotFoundError, EvidenceVerificationError)):
            verify_evidence(envelope, self.expected, trusted_producers=TRUST)

    def test_tampered_artifact_digest_is_rejected(self):
        self.artifact.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(EvidenceVerificationError, "digest"):
            verify_evidence(self.envelope(), self.expected, trusted_producers=TRUST)

    def test_parent_traversal_is_rejected_at_construction(self):
        with self.assertRaisesRegex(ValueError, "relative path"):
            self.envelope(artifact_path="../outside.txt")

    def test_artifact_outside_allowlist_is_rejected(self):
        (self.root / "private").mkdir()
        outside_allowlist = self.root / "private" / "result.txt"
        outside_allowlist.write_text("tests passed\n", encoding="utf-8")
        envelope = self.envelope(
            artifact_path="private/result.txt",
            artifact_sha256=hashlib.sha256(outside_allowlist.read_bytes()).hexdigest(),
        )
        with self.assertRaisesRegex(EvidenceVerificationError, "allowed paths"):
            verify_evidence(envelope, self.expected, trusted_producers=TRUST)

    def test_symlink_escape_is_rejected_when_symlinks_are_available(self):
        outside = Path(self.temp.name).parent / (Path(self.temp.name).name + "-outside.txt")
        outside.write_text("outside\n", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        link = self.root / "reports" / "escape.txt"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this platform")
        envelope = self.envelope(
            artifact_path="reports/escape.txt",
            artifact_sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
        )
        with self.assertRaisesRegex(EvidenceVerificationError, "outside repository"):
            verify_evidence(envelope, self.expected, trusted_producers=TRUST)

    def test_task_mismatch_is_rejected(self):
        with self.assertRaisesRegex(EvidenceVerificationError, "task_id"):
            verify_evidence(
                self.envelope(task_id="other-task"),
                self.expected,
                trusted_producers=TRUST,
            )

    def test_run_mismatch_is_rejected(self):
        with self.assertRaisesRegex(EvidenceVerificationError, "run_id"):
            verify_evidence(
                self.envelope(run_id="other-run"),
                self.expected,
                trusted_producers=TRUST,
            )

    def test_stale_source_sha_is_rejected(self):
        with self.assertRaisesRegex(EvidenceVerificationError, "source commit"):
            verify_evidence(
                self.envelope(source_commit_sha=QA_SOURCE),
                self.expected,
                trusted_producers=TRUST,
            )

    def test_untrusted_producer_is_rejected(self):
        with self.assertRaisesRegex(EvidenceVerificationError, "not trusted"):
            verify_evidence(
                self.envelope(producer_id="user-controlled"),
                self.expected,
                trusted_producers=TRUST,
            )

    def test_executor_cannot_claim_independent_qa(self):
        envelope = self.envelope(
            kind="independent_qa",
            producer_id="qa-service",
            producer_role="executor",
        )
        with self.assertRaisesRegex(EvidenceVerificationError, "executor"):
            verify_evidence(envelope, self.expected, trusted_producers=TRUST)

    def test_nonzero_exit_is_rejected(self):
        with self.assertRaisesRegex(EvidenceVerificationError, "did not exit"):
            verify_evidence(
                self.envelope(exit_code=2),
                self.expected,
                trusted_producers=TRUST,
            )

    def test_invalid_git_sha_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "full lowercase Git SHA"):
            self.envelope(source_commit_sha="latest")

    def test_no_allowlist_fails_closed(self):
        expectation = EvidenceExpectation(
            task_id="task-1",
            run_id="run-1",
            repo_root=str(self.root),
            source_commit_sha=SOURCE,
            allowed_paths=(),
        )
        with self.assertRaisesRegex(EvidenceVerificationError, "no allowed"):
            verify_evidence(self.envelope(), expectation, trusted_producers=TRUST)


if __name__ == "__main__":
    unittest.main()
