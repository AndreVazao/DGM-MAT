"""Evidence-safe language catalogue for Programming & Software Engineering.

This module describes language families and suggested validation stages only.
It does not assert that a compiler, interpreter, linter, SDK, or runtime is installed,
and it never executes source code.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath


@dataclass(frozen=True, slots=True)
class LanguageProfile:
    language_id: str
    display_name: str
    category: str
    extensions: tuple[str, ...]
    validation_stages: tuple[str, ...]
    execution_enabled: bool = False
    toolchain_status: str = "requires_environment_probe"


# Validation stages are recommendations, not proof that a tool is installed or run.
_PROFILES: tuple[LanguageProfile, ...] = (
    LanguageProfile("python", "Python", "programming", (".py", ".pyi"), ("syntax", "imports", "lint", "unit", "integration", "security")),
    LanguageProfile("javascript", "JavaScript", "programming", (".js", ".mjs", ".cjs", ".jsx"), ("syntax", "lint", "unit", "integration", "browser")),
    LanguageProfile("typescript", "TypeScript", "programming", (".ts", ".tsx"), ("typecheck", "lint", "unit", "integration", "browser")),
    LanguageProfile("html", "HTML", "markup", (".html", ".htm"), ("semantic_validation", "accessibility", "browser")),
    LanguageProfile("css", "CSS", "stylesheet", (".css",), ("syntax", "lint", "responsive", "accessibility", "browser")),
    LanguageProfile("scss", "SCSS", "stylesheet", (".scss", ".sass"), ("compile", "lint", "responsive", "browser")),
    LanguageProfile("sql", "SQL", "query", (".sql",), ("dialect_check", "migration_review", "integrity", "query_plan", "integration")),
    LanguageProfile("powershell", "PowerShell", "shell", (".ps1", ".psm1", ".psd1"), ("parse", "static_analysis", "dry_run", "windows_integration", "security")),
    LanguageProfile("bash", "Shell/Bash", "shell", (".sh", ".bash"), ("syntax", "static_analysis", "shellcheck_if_available", "dry_run", "integration")),
    LanguageProfile("java", "Java", "programming", (".java",), ("compile", "static_analysis", "unit", "integration", "security")),
    LanguageProfile("kotlin", "Kotlin", "programming", (".kt", ".kts"), ("compile", "static_analysis", "unit", "android_integration_if_applicable")),
    LanguageProfile("c", "C", "programming", (".c",), ("compile_warnings", "static_analysis", "unit", "memory_safety", "integration")),
    LanguageProfile("cpp", "C++", "programming", (".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"), ("compile_warnings", "static_analysis", "unit", "memory_safety", "integration")),
    LanguageProfile("c_cpp_header_ambiguous", "C/C++ header (ambiguous)", "ambiguous", (".h",), ("resolve_project_language_context", "compile", "static_analysis")),
    LanguageProfile("rust", "Rust", "programming", (".rs",), ("format", "compile", "clippy_if_available", "unit", "integration")),
    LanguageProfile("go", "Go", "programming", (".go",), ("format", "compile", "vet_if_available", "unit", "integration")),
    LanguageProfile("json", "JSON", "configuration", (".json",), ("parse", "schema_validation_if_defined", "secret_scan")),
    LanguageProfile("yaml", "YAML", "configuration", (".yaml", ".yml"), ("parse", "schema_validation_if_defined", "workflow_lint_if_applicable", "secret_scan")),
    LanguageProfile("toml", "TOML", "configuration", (".toml",), ("parse", "schema_validation_if_defined", "secret_scan")),
    LanguageProfile("xml", "XML", "configuration", (".xml",), ("parse", "schema_validation_if_defined", "external_entity_safety")),
)

_PROFILE_BY_ID = {profile.language_id: profile for profile in _PROFILES}
_PROFILE_BY_EXTENSION = {
    extension: profile
    for profile in _PROFILES
    for extension in profile.extensions
}


def list_language_profiles() -> tuple[LanguageProfile, ...]:
    """Return immutable profile records; no runtime/toolchain claims are made."""
    return _PROFILES


def get_language_profile(language_id: str) -> LanguageProfile | None:
    """Resolve a canonical language ID, case-insensitively."""
    if not isinstance(language_id, str):
        return None
    return _PROFILE_BY_ID.get(language_id.strip().casefold())


def language_for_path(path: str | PurePath) -> LanguageProfile | None:
    """Resolve by longest known suffix; unknown and extensionless paths return None."""
    if not isinstance(path, (str, PurePath)):
        return None
    name = PurePath(str(path).replace("\\", "/")).name.casefold()
    if not name or name in {".", ".."}:
        return None
    # Longest suffix wins (e.g. a future compound extension can safely override .ts).
    for extension in sorted(_PROFILE_BY_EXTENSION, key=len, reverse=True):
        if name.endswith(extension):
            return _PROFILE_BY_EXTENSION[extension]
    return None


def validation_plan_for_path(path: str | PurePath) -> dict[str, object]:
    """Return a planning-only validation checklist for a path, never an execution result."""
    profile = language_for_path(path)
    if profile is None:
        return {
            "path": str(path),
            "language_id": None,
            "status": "blocked_unknown_language",
            "execution_enabled": False,
            "toolchain_status": "not_probed",
            "validation_stages": ("identify_language_and_project_toolchain",),
        }
    return {
        "path": str(path),
        "language_id": profile.language_id,
        "display_name": profile.display_name,
        "status": "plan_only",
        "execution_enabled": profile.execution_enabled,
        "toolchain_status": profile.toolchain_status,
        "validation_stages": profile.validation_stages,
    }
