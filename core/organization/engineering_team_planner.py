"""Deterministic, planning-only engineering team decomposition.

The planner reuses the canonical language catalogue and organization Task model.
It creates proposed work items only: it does not assign workers, run code, mutate
repositories, invoke providers, or authorize execution.
"""
from __future__ import annotations

import hashlib
import ntpath
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

from core.development.language_catalog import language_for_path
from .models import Task


@dataclass(frozen=True, slots=True)
class EngineeringPlan:
    mission_id: str
    status: str
    tasks: tuple[Task, ...]
    recognized_paths: tuple[str, ...]
    blocked_paths: tuple[str, ...]
    language_ids: tuple[str, ...]
    notes: tuple[str, ...]


class EngineeringTeamPlanner:
    """Build a deterministic implementation/research/QA task graph.

    File extensions identify planning profiles only. They never establish that
    a compiler is installed or that an agent may execute a task.
    """

    IMPLEMENTATION_PERMISSION = "repo:write:sandbox"

    @staticmethod
    def _task_id(mission_id: str, stage: str, key: str = "") -> str:
        material = "\0".join((mission_id, stage, key)).encode("utf-8")
        return f"eng:{hashlib.sha256(material).hexdigest()[:24]}"

    @staticmethod
    def _safe_relative_path(raw_path: object) -> str | None:
        if not isinstance(raw_path, str):
            return None
        value = raw_path.strip().replace("\\", "/")
        if not value or "\0" in value:
            return None
        drive, _ = ntpath.splitdrive(value)
        path = PurePosixPath(value)
        if drive or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            return None
        normalized = path.as_posix()
        if normalized in {"", "."}:
            return None
        return normalized

    @staticmethod
    def _task(
        mission_id: str,
        stage: str,
        title: str,
        description: str,
        *,
        key: str = "",
        owner_department: str | None = None,
        dependencies: Iterable[str] = (),
        inputs: Iterable[str] = (),
        required_skills: Iterable[str] = (),
        required_permissions: Iterable[str] = (),
        metadata: dict | None = None,
        approval_required: bool = False,
    ) -> Task:
        task_metadata = {
            "planning_only": True,
            "execution_authorized": False,
            "toolchain_status": "not_probed",
            "team_stage": stage,
            "required_skills": sorted(set(required_skills)),
            "required_permissions": sorted(set(required_permissions)),
        }
        if metadata:
            task_metadata.update(metadata)
        # Callers may add descriptive metadata, but cannot override safety invariants.
        task_metadata["planning_only"] = True
        task_metadata["execution_authorized"] = False
        task_metadata["toolchain_status"] = "not_probed"
        task_metadata["team_stage"] = stage
        task_metadata["required_skills"] = sorted(set(required_skills))
        task_metadata["required_permissions"] = sorted(set(required_permissions))
        return Task(
            task_id=EngineeringTeamPlanner._task_id(mission_id, stage, key),
            title=title,
            mission_id=mission_id,
            description=description,
            owner_department=owner_department,
            dependencies=list(dependencies),
            inputs=list(inputs),
            approval_required=approval_required,
            approval_reason=(
                "Implementation remains a proposal until a separate governed "
                "execution approval is bound to an exact diff."
                if approval_required else None
            ),
            metadata=task_metadata,
        )

    def build_plan(
        self,
        *,
        mission_id: str,
        title: str,
        description: str,
        changed_paths: Iterable[str],
        risk_level: str = "normal",
        include_research: bool = False,
    ) -> EngineeringPlan:
        if not isinstance(mission_id, str) or not mission_id.strip():
            raise ValueError("mission_id is required")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title is required")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("description is required")
        if risk_level not in {"low", "normal", "high", "critical"}:
            raise ValueError("risk_level must be low, normal, high, or critical")
        if isinstance(changed_paths, (str, bytes)):
            raise TypeError("changed_paths must be an iterable of path strings")

        normalized: dict[str, str] = {}
        blocked: list[str] = []
        for raw in changed_paths:
            safe_path = self._safe_relative_path(raw)
            if safe_path is None:
                blocked.append(str(raw))
                continue
            normalized.setdefault(safe_path.casefold(), safe_path)

        groups: dict[str, list[str]] = {}
        unresolved: list[str] = []
        for path in sorted(normalized.values(), key=str.casefold):
            profile = language_for_path(path)
            if profile is None or profile.category == "ambiguous":
                unresolved.append(path)
                continue
            groups.setdefault(profile.language_id, []).append(path)

        tasks: list[Task] = []
        notes: list[str] = []
        if not groups:
            notes.append("No unambiguous supported file profile was found; no implementation task was created.")
            return EngineeringPlan(
                mission_id=mission_id,
                status="BLOCKED",
                tasks=(),
                recognized_paths=(),
                blocked_paths=tuple(sorted(set(blocked + unresolved), key=str.casefold)),
                language_ids=(),
                notes=tuple(notes),
            )

        research_id: str | None = None
        if include_research:
            research = self._task(
                mission_id,
                "research",
                f"Research: {title}",
                "Collect relevant official documentation and repository evidence. "
                "Separate verified facts, proposals and unknowns.",
                owner_department="research",
                required_skills=("technical-research", "source-provenance"),
                metadata={"external_calls_authorized": False},
            )
            tasks.append(research)
            research_id = research.task_id

        implementation_ids: list[str] = []
        for language_id, paths in sorted(groups.items()):
            dependencies = (research_id,) if research_id else ()
            task = self._task(
                mission_id,
                "implementation",
                f"{language_id} implementation",
                f"Prepare a bounded {language_id} change for: {', '.join(paths)}. "
                "Inspect callers and existing architecture before proposing a patch.",
                key=language_id,
                owner_department=None,
                dependencies=dependencies,
                inputs=paths,
                required_skills=(language_id,),
                required_permissions=("repo:read", self.IMPLEMENTATION_PERMISSION),
                metadata={
                    "language_id": language_id,
                    "source_paths": paths,
                    "patch_required": True,
                    "isolated_workspace_required": True,
                },
                approval_required=True,
            )
            tasks.append(task)
            implementation_ids.append(task.task_id)

        integration = self._task(
            mission_id,
            "integration-review",
            "Cross-language integration review",
            "Check contracts, schemas, imports, callers and compatibility across "
            "all implementation subtasks. Do not certify unexecuted checks.",
            owner_department=None,
            dependencies=implementation_ids,
            required_skills=("integration", "contracts"),
            required_permissions=("repo:read",),
            metadata={"independent_from_implementation": True},
        )
        tasks.append(integration)

        bug_hunt = self._task(
            mission_id,
            "bug-hunt",
            "Independent bug investigation",
            "Inspect the proposed changes and acceptance criteria independently; "
            "reproduce suspected defects and report evidence.",
            owner_department="bug-hunters",
            dependencies=(integration.task_id,),
            required_skills=("reproduction", "fault-isolation"),
            required_permissions=("repo:read", "tests:run"),
            metadata={"reviewer_must_differ_from_implementer": True},
        )
        qa = self._task(
            mission_id,
            "qa",
            "Independent testing and validation",
            "Run only configured, allowlisted checks in the exact isolated workspace; "
            "record commands, exit codes, revisions and evidence. Missing tools mean not_run.",
            owner_department="qa",
            dependencies=(integration.task_id,),
            required_skills=("testing", "independent-validation"),
            required_permissions=("repo:read", "tests:run"),
            metadata={"reviewer_must_differ_from_implementer": True},
        )
        tasks.extend((bug_hunt, qa))

        if risk_level in {"high", "critical"}:
            security = self._task(
                mission_id,
                "security-review",
                "Independent security review",
                "Review trust boundaries, permissions, secrets, dependency risk and "
                "negative tests before any promotion.",
                owner_department="security",
                dependencies=(integration.task_id,),
                required_skills=("security", "threat-model"),
                required_permissions=("repo:read", "tests:run"),
                metadata={"risk_level": risk_level, "independent_review": True},
            )
            tasks.append(security)

        blocked_paths = sorted(set(blocked + unresolved), key=str.casefold)
        if blocked_paths:
            notes.append("Some paths were excluded because they are unsafe, unknown, or ambiguous.")
        notes.append("All generated tasks are proposals; no worker was assigned and no code was executed.")
        return EngineeringPlan(
            mission_id=mission_id,
            status="PARTIAL" if blocked_paths else "PLAN_ONLY",
            tasks=tuple(tasks),
            recognized_paths=tuple(
                sorted(
                    (path for paths in groups.values() for path in paths),
                    key=str.casefold,
                )
            ),
            blocked_paths=tuple(blocked_paths),
            language_ids=tuple(sorted(groups)),
            notes=tuple(notes),
        )
