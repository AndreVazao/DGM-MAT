from __future__ import annotations

import json
import time

from core.api import runtime_api


def test_mission_page_returns_bounded_durable_summaries(monkeypatch, tmp_path):
    for index in range(3):
        mission_id = f"mission_{index + 1:08x}"
        payload = {
            "mission_id": mission_id,
            "goal": f"Inventory page {index}",
            "status": "COMPLETED",
            "progress": 100,
            "created_at": f"2026-11-03T10:0{index}:00+00:00",
            "updated_at": f"2026-11-03T10:0{index}:01+00:00",
            "metadata": {"result": {"handler": "list_repositories"}},
            "error": None,
        }
        (tmp_path / f"{mission_id}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        time.sleep(0.01)

    monkeypatch.setattr(runtime_api.mission_engine, "missions_path", tmp_path)

    first = runtime_api.list_missions_page(limit=2, offset=0)
    second = runtime_api.list_missions_page(limit=2, offset=2)

    assert first["total"] == 3
    assert first["offset"] == 0
    assert first["limit"] == 2
    assert len(first["items"]) == 2
    assert first["has_more"] is True
    assert first["next_offset"] == 2
    assert all(item["handler"] == "list_repositories" for item in first["items"])
    assert second["total"] == 3
    assert len(second["items"]) == 1
    assert second["has_more"] is False
    assert second["next_offset"] is None
    assert "logs" not in first["items"][0]
    assert "metadata" not in first["items"][0]
