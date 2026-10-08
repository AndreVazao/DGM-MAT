"""Governed pipeline for turning external/internal sources into DGM-MAT modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import copytree
import re

from .capability_models import CapabilityCandidate, CapabilityStatus


@dataclass(slots=True)
class ForgeResult:
    candidate_id: str
    status: CapabilityStatus
    snapshot_path: str
    module_path: str | None
    notes: list[str]


class SkillForge:
    """Prepare a source for reuse without direct imports.

    The forge deliberately separates:
    discovery -> snapshot -> adaptation -> validation -> promotion.
    Execution of untrusted source is outside this class and belongs to the
    sandbox/validation worker.
    """

    def __init__(self, staging_root: str | Path) -> None:
        self.staging_root = Path(staging_root)

    @staticmethod
    def _safe_id(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "candidate"

    def snapshot(self, candidate: CapabilityCandidate) -> Path:
        source = Path(candidate.source.locator)
        if not source.exists() or not source.is_dir():
            raise FileNotFoundError(source)
        target = self.staging_root / self._safe_id(candidate.candidate_id) / "source"
        target.parent.mkdir(parents=True, exist_ok=True)
        copytree(source, target, dirs_exist_ok=True)
        return target

    def create_adaptation_workspace(self, candidate: CapabilityCandidate) -> Path:
        workspace = self.staging_root / self._safe_id(candidate.candidate_id) / "adapted"
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def promote(self, candidate: CapabilityCandidate, adapted_module: str | Path, destination: str | Path) -> Path:
        module = Path(adapted_module)
        if not module.exists():
            raise FileNotFoundError(module)
        target = Path(destination) / self._safe_id(candidate.candidate_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        if module.is_dir():
            copytree(module, target, dirs_exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
            (target / module.name).write_bytes(module.read_bytes())
        return target
