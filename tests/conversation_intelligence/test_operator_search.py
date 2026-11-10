from pathlib import Path

from core.conversation_intelligence import operator_search


def test_extract_search_terms_removes_command_and_provider_words():
    assert operator_search.extract_search_terms(
        "busca conversas do ChatGPT sobre o projeto VAZAO EVSE"
    ) == ["VAZAO", "EVSE"]


def test_search_archives_and_writes_a_provenance_report(tmp_path, monkeypatch):
    calls = []

    def fake_search(term, provider, limit):
        calls.append((term, provider, limit))
        return {
            "results": [{
                "provider": "chatgpt",
                "source_id": "conversation-42",
                "title": "VAZAO EVSE architecture",
                "source_date": "2026-10-20",
                "match_type": "message",
                "snippet": f"Found {term} in the charging platform discussion.",
                "source_url": "https://chatgpt.com/c/42",
                "capture_status": "captured",
            }],
            "scanned_sources": 3,
            "scanned_bytes": 4096,
            "truncated": False,
        }

    monkeypatch.setattr(operator_search, "_search_archive_term", fake_search)
    monkeypatch.setenv("DGM_CONVERSATION_SEARCH_REPORT_DIR", str(tmp_path / "reports"))

    result = operator_search.search_archived_conversations(
        "busca conversas do ChatGPT sobre VAZAO EVSE"
    )

    assert calls == [("VAZAO", "chatgpt", 15), ("EVSE", "chatgpt", 15)]
    assert result["result_count"] == 1
    assert result["results"][0]["matched_terms"] == ["VAZAO", "EVSE"]
    assert result["provider_access_used"] is False
    assert result["full_history_verified"] is False
    report = Path(result["dossier_path"])
    assert report.is_file()
    content = report.read_text(encoding="utf-8")
    assert "conversation-42" in content
    assert "https://chatgpt.com/c/42" in content
    assert "histórico integral" in content
