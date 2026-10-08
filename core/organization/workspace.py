"""Shared workspace contract for the DGM-MAT digital organization."""

from __future__ import annotations

from pathlib import Path


class OrganizationWorkspace:
    """Creates the canonical shared workspace without deleting existing data."""

    ROOTS = (
        "missions",
        "tasks",
        "departments",
        "projects",
        "conversations",
        "artifacts",
        "decisions",
        "reports",
        "tests",
        "releases",
        "memory",
        "inbox",
        "outbox",
        "evidence",
        "agent_profiles",
        "evolution",
    )

    PROJECT_ROOTS = (
        "context",
        "recovered",
        "source",
        "architecture",
        "tests",
        "reports",
        "decisions",
        "artifacts",
        ".dgm",
    )

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def initialize(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in self.ROOTS:
            (self.root / name).mkdir(exist_ok=True)
        return self.root

    def initialize_project(self, project_id: str) -> Path:
        project_root = self.root / "projects" / project_id
        project_root.mkdir(parents=True, exist_ok=True)
        for name in self.PROJECT_ROOTS:
            (project_root / name).mkdir(exist_ok=True)
        return project_root

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)
