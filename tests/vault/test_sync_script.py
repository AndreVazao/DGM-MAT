from __future__ import annotations

import json
import sys

from scripts import sync_dgm_vault


class FakeVault:
    def __init__(self, root):
        self.root = root

    def register_known_projects(self):
        return []

    def get_project(self, project_id):
        return None

    def register_project(self, project_id, name, repository_path, aliases):
        return {"project_id": project_id, "name": name}

    def sync_completed_progress(self, progress_paths, providers=None):
        return {"imported": 0, "duplicates": 0, "failures": self.failures}

    def snapshot_repository(self, project_id, repository):
        return {"status": "created", "project_id": project_id}

    def summary(self):
        return {"projects": 1}


def _run(monkeypatch, tmp_path, failures):
    FakeVault.failures = failures
    monkeypatch.setattr(sync_dgm_vault, "VaultCatalog", FakeVault)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sync_dgm_vault.py",
            "--vault", str(tmp_path / "vault"),
            "--repository", str(tmp_path),
            "--progress-db", str(tmp_path / "progress.sqlite3"),
        ],
    )
    return sync_dgm_vault.main()


def test_sync_script_returns_success_when_no_import_failures(monkeypatch, tmp_path, capsys):
    assert _run(monkeypatch, tmp_path, []) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "completed"


def test_sync_script_returns_nonzero_when_import_failures_exist(monkeypatch, tmp_path, capsys):
    assert _run(monkeypatch, tmp_path, [{"source": "legacy", "error": "fixture"}]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "partial"
