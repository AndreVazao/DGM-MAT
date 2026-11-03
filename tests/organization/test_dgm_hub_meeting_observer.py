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
    assert meeting["events"][0]["source_sha256"] == meeting["events"][0]["event_id"]
    assert meeting["task_correlation"] == "conversation_only_task_id_not_exposed_by_hub"


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
    assert seen["url"] == "http://127.0.0.1:8770/api/history?limit=500"
    assert result["inserted"] == 2
    assert result["capture_mode"] == "read_only_poll"
    assert result["hub"] == "online"
    assert store.status()["captured_meetings"] == 1