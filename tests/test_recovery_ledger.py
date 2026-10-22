"""Tests for durable, forward-only recovery bookkeeping."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from core.recovery.recovery_ledger import (
    RecoveryLedger,
    RecoveryLedgerError,
    RecoverySource,
)


class RecoveryLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ledger = RecoveryLedger(self.root / "recovery.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def add(self, source_id: str, date: str, provider: str = "chatgpt") -> None:
        self.ledger.register(RecoverySource(
            provider=provider,
            source_id=source_id,
            title=f"Conversation {source_id}",
            source_date=date,
        ))

    def test_register_is_idempotent_for_provider_and_source_id(self) -> None:
        self.add("a", "2026-01-01")
        self.add("a", "2026-01-01")
        self.assertEqual(len(self.ledger.list_sources()), 1)

    def test_sources_are_claimed_in_deterministic_order(self) -> None:
        self.add("b", "2026-01-02")
        self.add("a", "2026-01-01")
        first = self.ledger.next_source()
        self.assertIsNotNone(first)
        self.assertEqual(first.source_id, "a")
        second = self.ledger.next_source()
        self.assertIsNotNone(second)
        self.assertEqual(second.source_id, "b")

    def test_restart_requeues_interrupted_source_once(self) -> None:
        self.add("a", "2026-01-01")
        self.add("b", "2026-01-02")
        # Simulate a previously completed later record so only "a" remains claimable.
        self.ledger.checkpoint("chatgpt", "b", capture_status="captured", completeness="unknown")
        self.assertEqual(self.ledger.next_source().source_id, "a")
        self.assertIsNone(self.ledger.next_source())
        self.assertEqual(self.ledger.recover_interrupted(), 1)
        self.assertEqual(self.ledger.next_source().source_id, "a")

    def test_partial_capture_does_not_trap_cursor_and_requires_explicit_retry(self) -> None:
        self.add("a", "2026-01-01")
        self.add("b", "2026-01-02")
        self.ledger.next_source()
        self.ledger.checkpoint("chatgpt", "a", capture_status="partial", detail="scroll incomplete")
        self.assertEqual(self.ledger.next_source().source_id, "b")
        self.ledger.request_retry("chatgpt", "a", "provider export now available")
        self.assertEqual(self.ledger.next_source().source_id, "a")

    def test_completed_source_advances_cursor_and_does_not_repeat(self) -> None:
        self.add("a", "2026-01-01")
        self.add("b", "2026-01-02")
        first = self.ledger.next_source()
        self.assertEqual(first.source_id, "a")
        self.ledger.checkpoint("chatgpt", "a", capture_status="captured", completeness="complete")
        next_item = self.ledger.next_source()
        self.assertEqual(next_item.source_id, "b")

    def test_failure_is_persisted_and_remains_retryable(self) -> None:
        self.add("a", "2026-01-01")
        self.ledger.next_source()
        self.ledger.checkpoint("chatgpt", "a", capture_status="failed", detail="source unavailable")
        saved = self.ledger.get("chatgpt", "a")
        self.assertEqual(saved.capture_status, "failed")
        self.assertEqual(saved.last_error, "source unavailable")
        self.assertIsNone(self.ledger.next_source())
        self.ledger.request_retry("chatgpt", "a", "provider access restored")
        self.assertEqual(self.ledger.next_source().source_id, "a")

    def test_retry_requires_a_reason_and_known_source(self) -> None:
        self.add("a", "2026-01-01")
        with self.assertRaises(ValueError):
            self.ledger.request_retry("chatgpt", "a", " ")
        with self.assertRaises(RecoveryLedgerError):
            self.ledger.request_retry("chatgpt", "missing", "new evidence")

    def test_verified_requires_archive_path_and_digest(self) -> None:
        self.add("a", "2026-01-01")
        with self.assertRaises(RecoveryLedgerError):
            self.ledger.checkpoint("chatgpt", "a", capture_status="verified")

    def test_invalid_digest_rejected(self) -> None:
        self.add("a", "2026-01-01")
        with self.assertRaises(ValueError):
            self.ledger.checkpoint(
                "chatgpt", "a", capture_status="captured", raw_sha256="not-a-hash"
            )

    def test_verified_archive_records_hash_and_source_remains_non_deletable(self) -> None:
        self.add("a", "2026-01-01")
        archive = self.root / "conversation.json"
        archive.write_text('{"messages":[]}', encoding="utf-8")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.ledger.checkpoint(
            "chatgpt", "a", capture_status="verified",
            completeness="complete", raw_archive_path=str(archive),
            raw_sha256=digest, index_status="indexed", repo_status="reconciled",
        )
        saved = self.ledger.get("chatgpt", "a")
        self.assertEqual(saved.raw_sha256, digest)
        self.assertEqual(saved.deletion_status, "not_eligible")

    def test_out_of_order_completion_does_not_skip_earlier_source(self) -> None:
        self.add("a", "2026-01-01")
        self.add("b", "2026-01-02")
        self.ledger.checkpoint("chatgpt", "b", capture_status="captured")
        self.assertEqual(self.ledger.next_source().source_id, "a")
        self.ledger.checkpoint("chatgpt", "a", capture_status="captured")
        self.assertIsNone(self.ledger.next_source())

    def test_verified_rejects_mismatched_archive_digest(self) -> None:
        self.add("a", "2026-01-01")
        archive = self.root / "conversation.json"
        archive.write_text('{"messages":[]}', encoding="utf-8")
        with self.assertRaises(RecoveryLedgerError):
            self.ledger.checkpoint(
                "chatgpt", "a", capture_status="verified",
                raw_archive_path=str(archive), raw_sha256="0" * 64,
            )

    def test_sql_pagination_preserves_stable_order(self) -> None:
        self.add("c", "2026-01-03")
        self.add("a", "2026-01-01")
        self.add("b", "2026-01-02")
        page = self.ledger.list_sources(limit=1, offset=1)
        self.assertEqual([item.source_id for item in page], ["b"])
        self.assertEqual(self.ledger.source_count(), 3)

    def test_status_counts_do_not_require_loading_source_objects(self) -> None:
        self.add("a", "2026-01-01")
        self.ledger.next_source()
        self.ledger.checkpoint("chatgpt", "a", capture_status="failed", detail="offline")
        self.add("b", "2026-01-02")
        self.assertEqual(self.ledger.status_counts(), {"discovered": 1, "failed": 1})

    def test_invalid_pagination_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.ledger.list_sources(limit=0)
        with self.assertRaises(ValueError):
            self.ledger.list_sources(offset=-1)

    def test_hash_file_matches_sha256(self) -> None:
        archive = self.root / "archive.bin"
        archive.write_bytes(b"DGM-MAT")
        self.assertEqual(
            self.ledger.sha256_file(archive),
            hashlib.sha256(b"DGM-MAT").hexdigest(),
        )

    def test_unknown_source_cannot_be_checkpointed(self) -> None:
        with self.assertRaises(RecoveryLedgerError):
            self.ledger.checkpoint("chatgpt", "missing", capture_status="captured")


if __name__ == "__main__":
    unittest.main()
