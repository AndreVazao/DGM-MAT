"""Bounded read-only mission capabilities backed by fixed local evidence sources."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


README_SECTIONS = (
    "Current role",
    "Operating principle",
    "Authority and architecture boundaries",
    "Current responsibilities",
    "Satellite and product boundaries",
)
CONSTITUTION_SECTIONS = (
    "2. Hierarquia de autoridade e comando",
    "3. Fronteiras dos repositórios",
    "3.4 Departamentos satélite",
    "4. Regras obrigatórias de dependência e comunicação",
)
MAX_SECTION_LINES = 10
MIN_SECTIONS = 4


def _extract_section(lines: list[str], expected_heading: str) -> dict[str, Any] | None:
    """Extract one exact Markdown heading and a bounded excerpt with source line numbers."""
    start_index = None
    heading_depth = 0
    for index, raw in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", raw.strip())
        if match and match.group(2).strip() == expected_heading:
            start_index = index
            heading_depth = len(match.group(1))
            break
    if start_index is None:
        return None

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s+.+$", lines[index].strip())
        if match and len(match.group(1)) <= heading_depth:
            end_index = index
            break

    body_start = start_index + 1
    body_end = end_index
    while body_start < body_end and not lines[body_start].strip():
        body_start += 1
    while body_end > body_start and not lines[body_end - 1].strip():
        body_end -= 1
    body = lines[body_start:body_end]
    # Bound the returned excerpt by physical source lines, preserving exact provenance.
    excerpt_lines = body[:MAX_SECTION_LINES]
    content = "\n".join(excerpt_lines)
    if not content.strip():
        return None
    if len(body) > MAX_SECTION_LINES:
        content += "\n… [excerpt truncated; consult the cited source for the complete section]"
    return {
        "heading": expected_heading,
        "start_line": body_start + 1,
        "end_line": body_start + len(excerpt_lines),
        "content": content,
    }


def build_architecture_summary(repo_root: str | Path) -> dict[str, Any]:
    """Summarize fixed local architecture documents without shell or network access."""
    root = Path(repo_root).resolve(strict=True)
    documents = (
        ("README.md", README_SECTIONS),
        (
            "docs/architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md",
            CONSTITUTION_SECTIONS,
        ),
    )
    sections: list[dict[str, Any]] = []
    source_files: list[str] = []

    for relative_path, headings in documents:
        source_path = (root / relative_path).resolve(strict=False)
        try:
            source_path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Architecture source escaped the repository root.") from exc
        if not source_path.is_file():
            continue
        try:
            lines = source_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"Architecture source is unreadable: {relative_path}") from exc

        file_has_sections = False
        for heading in headings:
            section = _extract_section(lines, heading)
            if section is None:
                continue
            sections.append({
                "path": relative_path,
                **section,
            })
            file_has_sections = True
        if file_has_sections:
            source_files.append(relative_path)

    if len(sections) < MIN_SECTIONS:
        raise ValueError(
            "Insufficient trusted architecture evidence: expected at least "
            f"{MIN_SECTIONS} readable sections, found {len(sections)}."
        )

    rendered = [
        "DGM-MAT architecture summary — read-only, evidence-backed",
        "No shell commands or external calls were used.",
        "",
    ]
    for section in sections:
        rendered.extend((
            f"## {section['heading']}",
            f"Source: {section['path']}:L{section['start_line']}-L{section['end_line']}",
            section["content"],
            "",
        ))

    return {
        "status": "completed",
        "summary": (
            f"Generated a bounded architecture summary from {len(sections)} source sections "
            f"across {len(source_files)} local documents."
        ),
        "output": "\n".join(rendered).strip(),
        "sources": [
            {
                "path": section["path"],
                "heading": section["heading"],
                "start_line": section["start_line"],
                "end_line": section["end_line"],
            }
            for section in sections
        ],
        "source_files": source_files,
        "read_only": True,
        "external_calls": 0,
        "commands_executed": 0,
    }
