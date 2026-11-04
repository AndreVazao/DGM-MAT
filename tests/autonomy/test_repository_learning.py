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
    assert record["tree_path"] is None
    assert "PRIVATE CONTENT" not in record["summary"]


def test_repository_learning_reports_missing_roots_without_failing(tmp_path: Path):
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[tmp_path / "missing"], batch_size=5
    )
    result = service.run_batch()
    assert result["status"] == "complete"
    assert result["total_candidates"] == 0
    assert result["root_warnings"] == [{"root": str(tmp_path / "missing"), "status": "missing"}]


def test_repository_learning_finds_git_worktrees_inside_hidden_workspace_folders(tmp_path):
    root = tmp_path / "workspace"
    repo = _create_repo(root / ".worktrees", "hidden-worktree")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5, max_depth=8
    )

    result = service.run_batch()
    records = service.list_repositories()

    assert result["cycle_complete"] is True
    assert result["progress_percent"] == 100.0
    assert len(records) == 1
    assert Path(records[0]["path"]) == repo


def test_repository_learning_generates_external_bounded_tree_without_secret_files(tmp_path: Path):
    root = tmp_path / "repos"
    repo = _create_repo(root, "tree-project")
    source = repo / "src"
    source.mkdir()
    (source / "main.py").write_text("print('not read')\n", encoding="utf-8")
    (repo / ".env").write_text("API_KEY=must-not-appear\n", encoding="utf-8")
    (repo / "service.pem").write_text("private key material\n", encoding="utf-8")
    (repo / "credentials.json").write_text('{"token":"must-not-appear"}\n', encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "dependency.js").write_text("// ignored\n", encoding="utf-8")

    ledger = tmp_path / "ledger"
    service = RepositoryLearningService(
        storage_dir=ledger, roots=[root], batch_size=5
    )
    result = service.run_batch()
    record = service.list_repositories()[0]

    assert result["cycle_complete"] is True
    tree_path = Path(record["tree_path"])
    assert tree_path.is_file()
    assert tree_path.parent == ledger / "trees"
    assert not tree_path.is_relative_to(repo)
    tree = tree_path.read_text(encoding="utf-8")
    assert "main.py" in tree
    assert ".env" not in tree
    assert "service.pem" not in tree
    assert "credentials.json" not in tree
    assert "node_modules" not in tree
    assert record["tree_entries"] >= 4
    assert record["tree_sha256"]
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert ".tree.txt" not in status


def test_repository_learning_reuses_existing_tree_for_unchanged_repository(tmp_path: Path):
    root = tmp_path / "repos"
    _create_repo(root, "stable-tree")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5, refresh_seconds=60
    )
    service.run_batch()
    first = service.list_repositories()[0]
    _expire_refresh(service)

    second_cycle = service.run_batch()
    second = service.list_repositories()[0]

    assert second_cycle["unchanged_skipped_this_cycle"] == 1
    assert second["tree_path"] == first["tree_path"]
    assert second["tree_generated_at"] == first["tree_generated_at"]


def test_repository_learning_groups_sibling_repositories_but_not_root_level_repositories(tmp_path: Path):
    root = tmp_path / "projects"
    grouped = root / "VAZAO-EVSE"
    _create_repo(grouped, "evse-firmware")
    _create_repo(grouped, "evse-cpms")
    _create_repo(root, "standalone-tool")

    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=10
    )
    service.run_batch()
    records = {item["name"]: item for item in service.list_repositories()}

    assert records["evse-firmware"]["project_group"] == "VAZAO-EVSE"
    assert records["evse-firmware"]["project_group_basis"] == "shared_parent_folder"
    assert records["evse-firmware"]["project_group_confidence"] == 0.85
    assert records["evse-cpms"]["project_group"] == "VAZAO-EVSE"
    assert records["standalone-tool"]["project_group"] == "standalone-tool"
    assert records["standalone-tool"]["project_group_basis"] == "single_repository_pending_semantic_review"


def test_repository_learning_groups_multiple_worktrees_by_same_git_origin(tmp_path: Path):
    root = tmp_path / "workspaces"
    first = _create_repo(root / "checkout-a", "shared-project")
    second = _create_repo(root / "checkout-b", "shared-project")
    for repo in (first, second):
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/shared-project.git"],
            check=True,
        )

    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=10
    )
    service.run_batch()
    records = service.list_repositories()

    assert len(records) == 2
    assert {item["project_group"] for item in records} == {"shared-project"}
    assert all(item["project_group_basis"] == "same_git_origin" for item in records)


def test_repository_learning_reads_only_indexed_tree_artifacts(tmp_path: Path):
    root = tmp_path / "repos"
    repo = _create_repo(root, "tree-reader")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5
    )
    service.run_batch()

    result = service.read_tree(str(repo))
    assert result["repo_path"] == str(repo.resolve())
    assert "README.md" in result["content"]
    assert result["tree_sha256"]

    try:
        service.read_tree(str(tmp_path / "unindexed"))
    except KeyError as exc:
        assert "repository_tree_not_found" in str(exc)
    else:
        raise AssertionError("unindexed repository paths must not expose arbitrary files")


def test_repository_learning_handles_unborn_empty_git_repositories(tmp_path: Path):
    root = tmp_path / "repos"
    repo = root / "empty-project"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "README.md").write_text("# Empty project\n\nA repository with no commit yet.\n", encoding="utf-8")

    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5
    )
    result = service.run_batch()
    record = service.list_repositories()[0]

    assert result["cycle_complete"] is True
    assert record["scan_status"] == "learned"
    assert record["head_sha"] == "unborn"
    assert record["tree_path"] is not None
    assert "repository with no commit" in record["summary"]


def test_repository_learning_does_not_reread_readme_for_unchanged_repositories(tmp_path: Path):
    root = tmp_path / "repos"
    _create_repo(root, "unchanged-readme")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5, refresh_seconds=60
    )
    service.run_batch()
    _expire_refresh(service)

    def fail_if_read(*_args, **_kwargs):
        raise AssertionError("unchanged README must not be read again")

    service._read_project_summary = fail_if_read
    result = service.run_batch()

    assert result["cycle_complete"] is True
    assert result["unchanged_skipped_this_cycle"] == 1


def test_repository_learning_command_timeout_is_configurable(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DGM_REPOSITORY_LEARNING_COMMAND_TIMEOUT", "8")
    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[tmp_path / "repos"]
    )
    assert service.command_timeout == 8.0


def test_repository_learning_does_not_group_owner_only_git_remotes(tmp_path: Path):
    root = tmp_path / "workspaces"
    first = _create_repo(root / "checkout-a", "project-a")
    second = _create_repo(root / "checkout-b", "project-b")
    for repo in (first, second):
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/AndreVazao/"],
            check=True,
        )

    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=10
    )
    service.run_batch()
    records = service.list_repositories()

    assert len(records) == 2
    assert all(
        item["project_group_basis"] == "single_repository_pending_semantic_review"
        for item in records
    )
    assert len({item["project_group_id"] for item in records}) == 2


def test_repository_tree_marks_depth_truncation(tmp_path: Path):
    root = tmp_path / "repos"
    repo = _create_repo(root, "deep-tree")
    folder = repo
    for index in range(1, 13):
        folder = folder / f"level-{index}"
        folder.mkdir()
    (folder / "beyond-depth.txt").write_text("not read by tree generation", encoding="utf-8")

    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5
    )
    service.run_batch()
    record = service.list_repositories()[0]
    tree = Path(record["tree_path"]).read_text(encoding="utf-8")

    assert record["tree_truncated"] is True
    assert "truncated: entry limit or maximum depth reached" in tree


def test_repository_tree_entry_limit_is_bounded_and_reported(tmp_path: Path, monkeypatch):
    import core.autonomy.repository_learning as repository_learning

    monkeypatch.setattr(repository_learning, "TREE_MAX_ENTRIES", 5)
    root = tmp_path / "repos"
    repo = _create_repo(root, "wide-tree")
    source = repo / "src"
    source.mkdir()
    for index in range(10):
        (source / f"module-{index:02}.py").write_text("# fixture\\n", encoding="utf-8")

    service = RepositoryLearningService(
        storage_dir=tmp_path / "ledger", roots=[root], batch_size=5
    )
    service.run_batch()
    record = service.list_repositories()[0]
    tree = Path(record["tree_path"]).read_text(encoding="utf-8")

    assert record["tree_entries"] == 5
    assert record["tree_truncated"] is True
    assert "truncated: entry limit or maximum depth reached" in tree
