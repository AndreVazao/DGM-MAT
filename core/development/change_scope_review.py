"""Small, deterministic scope/simplicity review for proposed code changes.

This is a review aid, not an AI code-quality oracle. It flags measurable scope
risks and requires human/owner review for unresolved complexity. It does not
edit files, merge code, run tests, or certify security.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class ChangeScope:
    requested_outcome: str
    allowed_paths: tuple[str, ...]
    changed_paths: tuple[str, ...]
    tested_paths: tuple[str, ...] = ()
    new_dependencies: tuple[str, ...] = ()
    duplicate_capabilities: tuple[str, ...] = ()
    justifications: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ScopeFinding:
    code: str
    severity: str
    message: str
    paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopeReview:
    findings: tuple[ScopeFinding, ...]

    @property
    def blocked(self) -> bool:
        return any(item.severity == "block" for item in self.findings)

    @property
    def requires_owner_review(self) -> bool:
        return any(item.severity in {"review", "block"} for item in self.findings)


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value and not path.is_absolute() and ".." not in path.parts and "\\" not in value)


def review_change_scope(scope: ChangeScope) -> ScopeReview:
    """Flag changes that exceed declared scope or add avoidable complexity.

    allowed_paths entries are exact paths or directory prefixes. New dependencies,
    overlapping capabilities, and untested changed paths require explicit
    justification; otherwise they block the proposed scope from passing review.
    """
    findings: list[ScopeFinding] = []
    if not isinstance(scope.requested_outcome, str) or not scope.requested_outcome.strip():
        findings.append(ScopeFinding("missing_outcome", "block", "A concrete requested outcome is required."))
    if not scope.allowed_paths:
        findings.append(ScopeFinding("missing_scope", "block", "No allowed paths were declared."))

    invalid = tuple(path for path in scope.allowed_paths + scope.changed_paths if not _safe_path(path))
    if invalid:
        findings.append(ScopeFinding("unsafe_path", "block", "Absolute paths and traversal are not allowed.", invalid))

    allowed = tuple(PurePosixPath(path) for path in scope.allowed_paths if _safe_path(path))
    out_of_scope = []
    for raw in scope.changed_paths:
        if not _safe_path(raw):
            continue
        path = PurePosixPath(raw)
        if not any(path == prefix or prefix in path.parents for prefix in allowed):
            out_of_scope.append(raw)
    if out_of_scope:
        findings.append(ScopeFinding("out_of_scope_change", "block", "Changed paths exceed the declared scope.", tuple(sorted(set(out_of_scope)))))

    untested = tuple(sorted(set(scope.changed_paths) - set(scope.tested_paths)))
    if untested:
        findings.append(ScopeFinding("untested_changes", "review", "Changed paths lack declared test coverage/evidence.", untested))

    justification = {key: value.strip() for key, value in scope.justifications if isinstance(key, str) and isinstance(value, str)}
    if scope.new_dependencies:
        missing = tuple(dep for dep in scope.new_dependencies if not justification.get("dependency:" + dep))
        if missing:
            findings.append(ScopeFinding("unjustified_dependency", "block", "Each new dependency needs a reason and alternatives considered.", missing))
        else:
            findings.append(ScopeFinding("new_dependency_review", "review", "New dependencies need security, licence and maintenance review.", tuple(scope.new_dependencies)))

    if scope.duplicate_capabilities:
        missing = tuple(cap for cap in scope.duplicate_capabilities if not justification.get("reuse:" + cap))
        if missing:
            findings.append(ScopeFinding("duplicate_capability", "block", "Reuse an existing capability unless a concrete gap is documented.", missing))
        else:
            findings.append(ScopeFinding("duplicate_capability_review", "review", "Documented overlap still needs owner approval.", tuple(scope.duplicate_capabilities)))

    if not findings:
        findings.append(ScopeFinding("minimal_scope", "pass", "No measurable scope/simplicity rule was violated; this is not a quality or security certification."))
    return ScopeReview(tuple(findings))
