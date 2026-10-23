"""Fail-closed validation for evidence manifests from development runs.

This module validates metadata and the referenced artifact. It does NOT execute
commands, authenticate a process, or prove that a command really ran. The
trusted_producers mapping must come from a future trusted internal adapter, not
from user-controlled request data. Do not treat this module alone as a security
boundary or wire it to user-facing VERIFIED transitions yet.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Mapping


_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_KINDS = {"validation", "independent_qa"}


@dataclass(frozen=True)
class EvidenceEnvelope:
    task_id: str
    run_id: str
    repo_root: str
    base_commit_sha: str
    source_commit_sha: str
    kind: str
    command_id: str
    exit_code: int
    artifact_path: str
    artifact_sha256: str
    producer_id: str
    producer_role: str

    def __post_init__(self) -> None:
        for name in (
            "task_id", "run_id", "repo_root", "command_id",
            "artifact_path", "producer_id", "producer_role",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.kind not in _ALLOWED_KINDS:
            raise ValueError("kind must be validation or independent_qa")
        if not isinstance(self.exit_code, int) or isinstance(self.exit_code, bool):
            raise ValueError("exit_code must be an integer")
        if not _GIT_SHA.fullmatch(self.base_commit_sha):
            raise ValueError("base_commit_sha must be a full lowercase Git SHA")
        if not _GIT_SHA.fullmatch(self.source_commit_sha):
            raise ValueError("source_commit_sha must be a full lowercase Git SHA")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ValueError("artifact_sha256 must be a full lowercase SHA-256 digest")
        relative = PurePosixPath(self.artifact_path)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ValueError("artifact_path must be a safe relative path")
        if "\\" in self.artifact_path or ":" in self.artifact_path:
            raise ValueError("artifact_path must use a relative POSIX path")


@dataclass(frozen=True)
class EvidenceExpectation:
    task_id: str
    run_id: str
    repo_root: str
    source_commit_sha: str
    allowed_paths: tuple[str, ...]


class EvidenceVerificationError(ValueError):
    """Evidence failed a fail-closed consistency or integrity check."""


def verify_evidence(
    envelope: EvidenceEnvelope,
    expected: EvidenceExpectation,
    *,
    trusted_producers: Mapping[str, tuple[str, ...]],
) -> Path:
    """Verify identity, scope, producer capability and artifact digest.

    trusted_producers maps producer IDs to the evidence kinds their trusted
    adapter is allowed to issue. It is an input from the caller, so arbitrary
    callers must not be allowed to supply or modify this mapping.
    """
    if envelope.task_id != expected.task_id:
        raise EvidenceVerificationError("task_id mismatch")
    if envelope.run_id != expected.run_id:
        raise EvidenceVerificationError("run_id mismatch")
    if envelope.source_commit_sha != expected.source_commit_sha:
        raise EvidenceVerificationError("stale or mismatched source commit")
    root = Path(expected.repo_root).resolve(strict=True)
    declared_root = Path(envelope.repo_root).resolve(strict=True)
    if not root.is_dir() or declared_root != root:
        raise EvidenceVerificationError("repository root mismatch")

    relative = PurePosixPath(envelope.artifact_path)
    allowed = tuple(PurePosixPath(item) for item in expected.allowed_paths)
    if not allowed:
        raise EvidenceVerificationError("no allowed artifact paths configured")
    if any(p.is_absolute() or ".." in p.parts or not p.parts for p in allowed):
        raise EvidenceVerificationError("invalid allowed-path policy")
    if not any(relative == item or item in relative.parents for item in allowed):
        raise EvidenceVerificationError("artifact path is outside allowed paths")

    artifact = (root / Path(*relative.parts)).resolve(strict=True)
    try:
        artifact.relative_to(root)
    except ValueError as exc:
        raise EvidenceVerificationError("artifact resolves outside repository root") from exc
    if not artifact.is_file():
        raise EvidenceVerificationError("artifact is not a regular file")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if digest != envelope.artifact_sha256:
        raise EvidenceVerificationError("artifact digest mismatch")
    if envelope.exit_code != 0:
        raise EvidenceVerificationError("evidence command did not exit successfully")

    capabilities = trusted_producers.get(envelope.producer_id)
    if capabilities is None or envelope.kind not in capabilities:
        raise EvidenceVerificationError("producer is not trusted for this evidence kind")
    if envelope.kind == "independent_qa" and envelope.producer_role in {
        "executor", "implementation", "worker", "developer"
    }:
        raise EvidenceVerificationError("executor cannot issue independent QA evidence")
    if envelope.kind == "validation" and envelope.producer_role in {
        "executor", "implementation", "worker", "developer"
    }:
        raise EvidenceVerificationError("executor cannot issue validation evidence")
    return artifact
