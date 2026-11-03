from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from core.autonomy.repository_learning import RepositoryLearningService


def _create_repo(path: Path, name: str) -> Path:
    repo = path / name
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "DGM Test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "dgm-test@example.invalid"], check=True)
    (repo / "README.md").write_text(f"# {name}\n\nA bounded repository-learning fixture.\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md", "pyproject.toml"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "initial fixture"], check=True)
    return repo


def _expire_refresh(service: RepositoryLearningService) -> None:
    with service._connection() as db:
        row = db.execute(
            "SELECT value_json FROM learning_state WHERE state_key='active'"
        ).fetchone()
        state = json.loads(row["value_json"])
        state["next_refresh_at"] = "2000-01-01T00:00:00+00:00"
        db.execute(
            "UPDATE learning_state SET value_json=? WHERE state_key='active'",
            (json.dumps(state),),
        )


def test_repository_learning_persists_cursor_and_resumes_without_repeating(tmp_path: Path):
    root = tmp_path / "repos"
    first = _create_repo(root, "alpha")
    _create_repo(root, "bravo")
    _create_repo(root, "charlie")
    ledger = tmp_path / "ledger"

    service = RepositoryLearningService(
        storage_dir=ledger, roots=[root], batch_size=1, refresh_seconds=3600
    )
    first_page = service.run_batch()
    assert first_page["status"] == "running"
    assert first_page["processed_candidates"] == 1
    assert first_page["pending_candidates"] == 2

    resumed = RepositoryLearningService(
        storage_dir=ledger, roots=[root], batch_size=1, refresh_seconds=3600
    )
    second_page = resumed.run_batch()
    assert second_page["processed_candidates"] == 2
    assert second_page["pending_candidates"] == 1

    final_page = resumed.run_batch()
    assert final_page["cycle_complete"] is True
    assert final_page["repositories_learned"] == 3
    records = {item["name"]: item for item in resumed.list_repositories()}
    assert records["alpha"]["scan_count"] == 1
    assert records["alpha"]["head_sha"]
    assert records["alpha"]["stack"] == ["pyproject.toml"]
    assert "bounded repository-learning fixture" in records["alpha"]["summary"]
    before = subprocess.run(
        ["git", "-C", str(first), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert before == ""


def test_repository_learning_skips_unchanged_repositories_and_refreshes_changed_head(tmp_path: Path):
    root = tmp_path / "repos"
    repo = _create_repo(root, "project")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5, refresh_seconds=60
    )
    first = service.run_batch()
    assert first["repositories_learned"] == 1
    _expire_refresh(service)

    unchanged = service.run_batch()
    assert unchanged["cycle_complete"] is True
    assert unchanged["unchanged_skipped_this_cycle"] == 1
    assert service.list_repositories()[0]["scan_count"] == 1

    (repo / "README.md").write_text("# project\n\nUpdated project purpose.\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "update purpose"], check=True)
    _expire_refresh(service)

    changed = service.run_batch()
    record = service.list_repositories()[0]
    assert changed["inspected_this_cycle"] == 1
    assert record["scan_count"] == 2
    assert "Updated project purpose" in record["summary"]


def test_protected_full_mirror_is_recorded_without_reading_readme(tmp_path: Path):
    root = tmp_path / "repos"
    protected = _create_repo(root, "DGM-MAT-FULL-MIRROR")
    (protected / "README.md").write_text("# PRIVATE CONTENT MUST NOT BE INGESTED\n", encoding="utf-8")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5
    )

    result = service.run_batch()
    record = service.list_repositories()[0]
    assert result["cycle_complete"] is True
    assert record["protected"] is True
    assert record["scan_status"] == "protected_metadata_only"
    assert "PRIVATE CONTENT" not in record["summary"]


def test_repository_learning_reports_missing_roots_without_failing(tmp_path: Path):
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[tmp_path / "missing"], batch_size=5
    )
    result = service.run_batch()
    assert result["status"] == "complete"
    assert result["total_candidates"] == 0
    assert result["root_warnings"] == [{"root": str(tmp_path / "missing"), "status": "missing"}]
