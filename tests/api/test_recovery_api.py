"""Tests for the read-only recovery inventory API."""
from __future__ import annotations

import hashlib
from pathlib import Path

from core.api import recovery_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.recovery_ledger import RecoveryLedger, RecoverySource


def test_recovery_routes_are_operator_only():
    assert classify_request_path("/recovery/status", "GET").scope is SecurityScope.OPERATOR
    assert classify_request_path("/recovery/sources", "GET").scope is SecurityScope.OPERATOR
    assert classify_request_path("/recovery/sources", "POST") is None


def test_status_reports_shared_browser_capture_api_without_provider_or_deletion(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    ledger.register(RecoverySource(
        provider="chatgpt",
        source_id="conversation-1",
        title="Project discussion",
        source_date="2026-10-01",
    ))
    monkeypatch.setattr(recovery_api, "get_recovery_ledger", lambda: ledger)
    monkeypatch.delenv("DGM_CHROME_EXTENSION_ID", raising=False)

    result = recovery_api.recovery_status()

    assert result["source_count"] == 1
    assert result["capture_status_counts"] == {"discovered": 1}
    assert result["provider_connectors_enabled"] is False
    assert result["provider_deletion_enabled"] is False
    assert result["browser_ui_capture_api"] is True
    assert result["browser_extension_origin_configured"] is False
    assert result["browser_ui_pairing_ready"] is False
    assert result["integration_status"] == "ledger_and_browser_ui_api"


def test_source_inventory_is_paginated_and_excludes_transcript_body(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    for index in range(3):
        ledger.register(RecoverySource(
            provider="chatgpt",
            source_id=f"conversation-{index}",
            title=f"Title {index}",
            source_date=f"2026-10-0{index + 1}",
        ))
    monkeypatch.setattr(recovery_api, "get_recovery_ledger", lambda: ledger)

    page = recovery_api.list_recovery_sources(limit=2, offset=1)

    assert page["total"] == 3
    assert page["limit"] == 2
    assert len(page["items"]) == 2
    assert page["items"][0]["source_id"] == "conversation-1"
    assert all("transcript" not in item and "messages" not in item for item in page["items"])


def test_inventory_exposes_hash_metadata_not_archive_contents(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    archive = tmp_path / "raw.json"
    archive.write_text('{"messages":["private transcript"]}', encoding="utf-8")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    ledger.register(RecoverySource(
        provider="chatgpt",
        source_id="conversation-1",
        title="Project discussion",
        source_date="2026-10-01",
        raw_archive_path=str(archive),
        raw_sha256=digest,
    ))
    monkeypatch.setattr(recovery_api, "get_recovery_ledger", lambda: ledger)

    result = recovery_api.list_recovery_sources(limit=10, offset=0)

    assert result["items"][0]["raw_sha256"] == digest
    assert "private transcript" not in str(result)



def test_github_reference_routes_are_operator_only():
    expected = (
        ("/recovery/github-references", "GET"),
        ("/recovery/github-references/verify", "POST"),
    )
    for path, method in expected:
        route = classify_request_path(path, method)
        assert route is not None
        assert route.scope is SecurityScope.OPERATOR


def test_chrome_import_route_is_operator_only_and_preserves_source_contract(monkeypatch):
    class FakeImporter:
        def import_inbox(self):
            return {
                "status": "completed",
                "files_imported": 1,
                "source_files_modified": 0,
            }

    monkeypatch.setattr(recovery_api, "ChromeConversationArchiveImporter", FakeImporter)
    route = classify_request_path("/recovery/chrome/import", "POST")
    result = recovery_api.import_chrome_conversation_archive()

    assert route is not None and route.scope is SecurityScope.OPERATOR
    assert result["status"] == "completed"
    assert result["source_files_modified"] == 0
