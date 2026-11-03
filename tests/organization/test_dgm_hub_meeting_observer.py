from __future__ import annotations

import json

import pytest

from core.organization.dgm_hub_meeting_observer import (
    DGMHubMeetingObserver,
    HubMeetingStore,
    HubObserverError,
    _NoRedirectHandler,
)


def _events():
    return [
        {
            "timestamp": "2026-11-03T11:00:00+00:00",
            "kind": "user_message",
            "conversation_id": "meeting-1",
            "message": "Vamos avaliar a arquitetura.",
            "targets": ["codex", "llm7"],
        },
        {
            "timestamp": "2026-11-03T11:00:05+00:00",
            "kind": "provider_response",
            "conversation_id": "meeting-1",
            "provider": "llm7",
            "status": "ok",
            "text": "Recomendo separar captura e decisão.",
        },
    ]


def test_ingest_is_idempotent_and_preserves_source_provenance(tmp_path):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    events = _events()

    first = store.ingest(events)
    second = store.ingest(events)

    assert first["inserted"] == 2
    assert first["duplicates"] == 0
    assert second["inserted"] == 0
    assert second["duplicates"] == 2

    meeting = store.get_meeting("meeting-1")
    assert meeting is not None
    assert meeting["event_count"] == 2
    assert meeting["objective"] == "Vamos avaliar a arquitetura."
    assert meeting["targets"] == ["codex", "llm7"]
    assert [event["actor"] for event in meeting["events"]] == ["operator", "llm7"]
    assert meeting["events"][0]["event_id"] == "legacy_" + meeting["events"][0]["source_sha256"]
    assert meeting["task_correlation"] == "legacy_unlinked"


def test_secret_like_text_is_redacted_but_original_fingerprint_is_retained(tmp_path):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    event = {
        "timestamp": "2026-11-03T11:00:00+00:00",
        "kind": "user_message",
        "conversation_id": "secret-test",
        "message": "api_key=abcdef1234567890 DGM_GOVERNANCE_OWNER_TOKEN=ownersecret123456 Bearer abcdefghijklmnopqrstuvwxyz012345",
    }
    expected_fingerprint = store.event_fingerprint(event)

    store.ingest([event])
    captured = store.get_meeting("secret-test")["events"][0]

    assert captured["source_sha256"] == expected_fingerprint
    stored_text = captured["payload"]["message"]
    assert "abcdef1234567890" not in stored_text
    assert "ownersecret123456" not in stored_text
    assert "abcdefghijklmnopqrstuvwxyz012345" not in stored_text
    assert "[REDACTED]" in stored_text


def test_invalid_events_are_counted_and_not_persisted(tmp_path):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    result = store.ingest([None, {}, {"kind": "user_message"}])

    assert result["invalid"] == 3
    assert result["inserted"] == 0
    assert store.status()["captured_events"] == 0


def test_observer_rejects_non_loopback_or_wrong_port(tmp_path):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")

    with pytest.raises(HubObserverError):
        DGMHubMeetingObserver(store, "http://192.168.1.20:8770")

    with pytest.raises(HubObserverError):
        DGMHubMeetingObserver(store, "http://127.0.0.1:8080")


def test_observer_capture_once_uses_read_only_history_endpoint(tmp_path, monkeypatch):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    observer = DGMHubMeetingObserver(store)
    payload = json.dumps({"events": _events()}).encode("utf-8")

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return payload

    seen = {}

    class FakeOpener:
        def open(self, request, timeout):
            seen["method"] = request.get_method()
            seen["url"] = request.full_url
            seen["timeout"] = timeout
            return Response()

    def fake_build_opener(*handlers):
        seen["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(
        "core.organization.dgm_hub_meeting_observer.urllib.request.build_opener",
        fake_build_opener,
    )

    result = observer.capture_once()

    assert seen["method"] == "GET"
    redirect_handler = next(item for item in seen["handlers"] if isinstance(item, _NoRedirectHandler))
    assert redirect_handler.redirect_request(None, None, 302, "Found", {}, "https://example.com") is None
    assert any(type(item).__name__ == "ProxyHandler" for item in seen["handlers"])
    assert seen["url"] == "http://127.0.0.1:8770/api/history?after=0&limit=500"
    assert result["inserted"] == 2
    assert result["capture_mode"] == "read_only_poll"
    assert result["pagination_supported"] is False
    assert result["hub"] == "online"
    assert store.status()["captured_meetings"] == 1


def _cursor_event(seq: int, kind: str, *, task_id: str = "task-1", provider: str | None = None):
    event = {
        "event_id": f"hub-event-{seq}",
        "seq": seq,
        "timestamp": f"2026-11-03T12:00:{seq:02d}+00:00",
        "kind": kind,
        "conversation_id": "cursor-meeting",
        "task_id": task_id,
    }
    if provider:
        event["provider"] = provider
    if kind == "user_message":
        event["message"] = "Discutir arquitetura"
        event["targets"] = ["codex", "llm7"]
    else:
        event["status"] = "timeout" if kind == "provider_error" else "ok"
        event["text"] = f"resultado {seq}"
    return event


def test_observer_follows_multiple_cursor_pages_and_persists_task_event_ids(tmp_path, monkeypatch):
    from urllib.parse import parse_qs, urlsplit

    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    observer = DGMHubMeetingObserver(store)
    pages = {
        "0": {
            "events": [
                _cursor_event(1, "user_message"),
                _cursor_event(2, "provider_response", provider="llm7"),
            ],
            "next_cursor": "2",
            "has_more": True,
        },
        "2": {
            "events": [
                _cursor_event(3, "provider_error", provider="codex"),
                _cursor_event(4, "provider_response", provider="kilo"),
            ],
            "next_cursor": "4",
            "has_more": False,
        },
    }
    seen = []

    class Response:
        status = 200

        def __init__(self, payload):
            self.payload = json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return self.payload

    class FakeOpener:
        def open(self, request, timeout):
            query = parse_qs(urlsplit(request.full_url).query)
            cursor = query["after"][0]
            seen.append((request.get_method(), cursor, timeout))
            return Response(pages[cursor])

    monkeypatch.setattr(
        "core.organization.dgm_hub_meeting_observer.urllib.request.build_opener",
        lambda *_handlers: FakeOpener(),
    )

    result = observer.capture_once()

    assert seen == [("GET", "0", observer.request_timeout), ("GET", "2", observer.request_timeout)]
    assert result["pagination_supported"] is True
    assert result["pages"] == 2
    assert result["received"] == 4
    assert result["inserted"] == 4
    assert result["has_more"] is False
    assert result["next_cursor"] == "4"
    assert store.get_state("last_cursor")["cursor"] == "4"
    assert store.status()["captured_events"] == 4

    meeting = store.get_meeting("cursor-meeting")
    assert meeting["task_correlation"] == "complete"
    assert [event["event_id"] for event in meeting["events"]] == [
        "hub-event-1", "hub-event-2", "hub-event-3", "hub-event-4"
    ]
    assert [event["source_seq"] for event in meeting["events"]] == [1, 2, 3, 4]
    assert meeting["events"][2]["kind"] == "provider_error"
    assert meeting["events"][2]["actor"] == "codex"
    assert store.list_meetings()[0]["provider_errors"] == 1

    reopened = HubMeetingStore(tmp_path / "hub.sqlite3")
    assert reopened.get_state("last_cursor")["cursor"] == "4"


def test_observer_refuses_non_advancing_cursor_without_persisting_it(tmp_path, monkeypatch):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    observer = DGMHubMeetingObserver(store)
    payload = json.dumps({
        "events": [_cursor_event(1, "user_message")],
        "next_cursor": "0",
        "has_more": True,
    }).encode("utf-8")

    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self, _limit):
            return payload

    class FakeOpener:
        def open(self, _request, timeout):
            return Response()

    monkeypatch.setattr(
        "core.organization.dgm_hub_meeting_observer.urllib.request.build_opener",
        lambda *_handlers: FakeOpener(),
    )

    with pytest.raises(HubObserverError, match="cursor did not advance"):
        observer.capture_once()

    assert store.get_state("last_cursor") is None
    assert store.status()["captured_events"] == 0


def test_existing_observer_database_upgrades_legacy_fingerprint_rows_in_place(tmp_path):
    import sqlite3

    database = tmp_path / "hub.sqlite3"
    legacy_event = {
        "timestamp": "2026-11-03T11:00:00+00:00",
        "kind": "user_message",
        "conversation_id": "legacy-meeting",
        "message": "Mensagem antiga",
    }
    fingerprint = HubMeetingStore.event_fingerprint(legacy_event)
    connection = sqlite3.connect(database)
    connection.executescript("""
        CREATE TABLE hub_meeting_events (
            event_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            event_kind TEXT NOT NULL,
            actor TEXT NOT NULL,
            provider_id TEXT,
            task_id TEXT,
            source_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            schema_version INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE hub_observer_state (
            state_key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    connection.execute("""
        INSERT INTO hub_meeting_events (
            event_id, conversation_id, occurred_at, event_kind, actor,
            provider_id, task_id, source_sha256, payload_json, captured_at, schema_version
        ) VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, 1)
    """, (
        fingerprint, "legacy-meeting", legacy_event["timestamp"], "user_message",
        "operator", fingerprint, json.dumps(legacy_event), "2026-11-03T11:01:00+00:00",
    ))
    connection.commit()
    connection.close()

    store = HubMeetingStore(database)
    migrated = store.get_event("legacy_" + fingerprint)
    assert migrated is not None
    assert migrated["local_event_key"] == fingerprint
    assert migrated["source_seq"] is None

    enriched = {
        **legacy_event,
        "event_id": "hub-event-legacy-1",
        "seq": 1,
        "correlation_status": "legacy_unlinked",
    }
    result = store.ingest([enriched])

    assert result["upgraded_legacy"] == 1
    assert result["inserted"] == 1
    assert store.status()["captured_events"] == 1
    upgraded = store.get_event("hub-event-legacy-1")
    assert upgraded["event_id"] == "hub-event-legacy-1"
    assert upgraded["local_event_key"] == fingerprint
    assert upgraded["source_seq"] == 1


def test_stable_hub_event_id_prevents_payload_overwrite_on_retry(tmp_path):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    first = _cursor_event(1, "user_message")
    retry = {**first, "message": "altered retry payload"}

    initial = store.ingest([first])
    repeated = store.ingest([retry])

    assert initial["inserted"] == 1
    assert repeated["duplicates"] == 1
    assert store.status()["captured_events"] == 1
    stored = store.get_event("hub-event-1")
    assert stored["payload"]["message"] == "Discutir arquitetura"



def test_invalid_cursor_page_does_not_advance_persisted_cursor(tmp_path):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    result = store.ingest([None], next_cursor="1", has_more=False)

    assert result["invalid"] == 1
    assert result["cursor_persisted"] is False
    assert store.get_state("last_cursor") is None


def test_observer_detects_hub_journal_reset_without_rewinding_cursor(tmp_path, monkeypatch):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    store.set_state("last_cursor", {"cursor": "52", "has_more": False})
    observer = DGMHubMeetingObserver(store)
    payload = json.dumps({
        "events": [],
        "next_cursor": "52",
        "has_more": False,
        "total_events": 0,
    }).encode("utf-8")

    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self, _limit):
            return payload

    class FakeOpener:
        def open(self, _request, timeout):
            return Response()

    monkeypatch.setattr(
        "core.organization.dgm_hub_meeting_observer.urllib.request.build_opener",
        lambda *_handlers: FakeOpener(),
    )

    with pytest.raises(HubObserverError, match="Manual reconciliation is required"):
        observer.capture_once()

    assert store.get_state("last_cursor")["cursor"] == "52"
    assert store.status()["captured_events"] == 0
