from __future__ import annotations

import time
from pathlib import Path

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


def _engine(roots: list[Path], monkeypatch) -> MissionEngine:
    engine = MissionEngine.__new__(MissionEngine)
    engine.REPO_SCAN_ROOTS = roots
    engine.MISSION_EXECUTION_TIMEOUT_SECONDS = 60.0
    return engine


def _make_repos(root: Path, names: list[str]) -> None:
    for name in names:
        (root / name / ".git").mkdir(parents=True)


def _fake_inspector(path: Path, repo_started: float, mission_started: float):
    return {
        "name": path.name,
        "path": str(path),
        "branch": "main",
        "branches": ["main"],
        "branches_truncated": False,
        "last_commit": "abc1234",
        "uncommitted_changes": 0,
        "git_status": "clean",
    }


def test_repository_pages_are_stable_bounded_and_have_no_duplicates(tmp_path, monkeypatch):
    root = tmp_path / "repos"
    root.mkdir()
    _make_repos(root, ["Echo", "Alpha", "Delta", "Charlie", "Bravo"])
    engine = _engine([root, root], monkeypatch)
    monkeypatch.setattr(engine, "_inspect_git_repository", _fake_inspector)

    first, first_meta = engine._discover_workspace_repositories(time.monotonic(), offset=0, page_size=2)
    second, second_meta = engine._discover_workspace_repositories(
        time.monotonic(), offset=first_meta["next_cursor"], page_size=2
    )
    third, third_meta = engine._discover_workspace_repositories(
        time.monotonic(), offset=second_meta["next_cursor"], page_size=2
    )

    assert [item["name"] for item in first] == ["Alpha", "Bravo"]
    assert [item["name"] for item in second] == ["Charlie", "Delta"]
    assert [item["name"] for item in third] == ["Echo"]
    all_names = [item["name"] for page in (first, second, third) for item in page]
    assert len(all_names) == len(set(all_names)) == 5
    assert first_meta["total_candidates"] == 5
    assert first_meta["next_cursor"] == 2
    assert first_meta["repos_skipped"] == 3
    assert second_meta["current_page"] == 2
    assert second_meta["next_cursor"] == 4
    assert third_meta["current_page"] == 3
    assert third_meta["next_cursor"] is None
    assert third_meta["complete"] is True


def test_default_roots_preserve_existing_locations_and_include_ai():
    roots = {str(path).replace("\\", "/").casefold() for path in MissionEngine.REPO_SCAN_ROOTS}
    assert "c:/programasgodmode" in roots
    assert "c:/devopgodmode" in roots
    assert "c:/ai" in roots


def test_environment_roots_extend_defaults_and_are_deduplicated(tmp_path, monkeypatch):
    default_root = tmp_path / "default"
    extra_root = tmp_path / "extra"
    default_root.mkdir()
    extra_root.mkdir()
    engine = _engine([default_root], monkeypatch)
    monkeypatch.setenv("DGM_REPO_SCAN_ROOTS", f"{extra_root};{default_root}")

    roots = engine._repository_scan_roots()

    assert len(roots) == 2
    assert {path.resolve() for path in roots} == {default_root.resolve(), extra_root.resolve()}


def test_missing_root_is_reported_and_inventory_is_not_claimed_complete(tmp_path, monkeypatch):
    root = tmp_path / "repos"
    root.mkdir()
    _make_repos(root, ["One"])
    missing = tmp_path / "missing"
    engine = _engine([root, missing], monkeypatch)
    monkeypatch.setattr(engine, "_inspect_git_repository", _fake_inspector)

    repositories, meta = engine._discover_workspace_repositories(time.monotonic(), page_size=20)

    assert len(repositories) == 1
    assert meta["complete"] is False
    assert meta["partial"] is True
    assert meta["root_warnings"] == [{"root": str(missing.resolve()), "status": "missing"}]


def test_mission_result_exposes_page_cursor_and_partial_status(tmp_path, monkeypatch):
    root = tmp_path / "repos"
    root.mkdir()
    _make_repos(root, ["One", "Two", "Three"])
    engine = _engine([root], monkeypatch)
    monkeypatch.setattr(engine, "_inspect_git_repository", _fake_inspector)
    mission = Mission(
        mission_id="mission_1234abcd",
        goal="Lista os repositórios locais",
        description="Repository page contract",
        status=MissionStatus.RUNNING,
        metadata={"repository_page": {"offset": 1, "page_size": 1}},
    )

    result = engine._execute_list_repositories_mission(mission)

    assert result["count"] == 1
    assert result["pagination"] == {
        "total_candidates": 3,
        "current_page": 2,
        "page_size": 1,
        "page_offset": 1,
        "next_cursor": 2,
        "has_more": True,
        "complete": False,
    }
    assert result["repos_skipped"] == 1
    assert result["partial"] is True


def test_mission_create_persists_page_parameters_before_queueing(monkeypatch):
    class Queue:
        def enqueue(self, action_type, payload):
            return 91

        def approve(self, action_id, operator):
            return True

    engine = MissionEngine.__new__(MissionEngine)
    engine.action_queue = Queue()
    engine.active_missions = {}
    monkeypatch.setattr(engine, "save_mission", lambda mission: None)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(
        engine,
        "_update_status",
        lambda mission, status: setattr(mission, "status", status),
    )

    mission = engine.create_mission(
        "Lista os repositórios locais",
        "Request page 3",
        repository_page={"offset": 40, "page_size": 10},
    )

    assert mission.metadata["repository_page"] == {"offset": 40, "page_size": 10}
    assert mission.metadata["action_id"] == 91
