from pathlib import Path

import pytest

from core.autonomy.mission_capabilities import build_architecture_summary


def test_architecture_summary_uses_fixed_sources_and_line_provenance(tmp_path):
    root = tmp_path
    (root / "docs/architecture").mkdir(parents=True)
    (root / "README.md").write_text(
        "# DGM-MAT\n\n## Current role\n\nCentral brain.\n\n"
        "## Operating principle\n\nObserve, audit, plan, validate.\n\n"
        "## Authority and architecture boundaries\n\nThe cockpit is presentation-only.\n\n"
        "## Current responsibilities\n\nCoordinate missions.\n",
        encoding="utf-8",
    )
    constitution = root / "docs/architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md"
    constitution.write_text(
        "# Constitution\n\n## 2. Hierarquia de autoridade e comando\n\nHuman owner is final authority.\n\n"
        "## 3. Fronteiras dos repositórios\n\nKeep the core modular.\n\n"
        "### 3.4 Departamentos satélite\n\nDepartments have explicit boundaries.\n",
        encoding="utf-8",
    )

    result = build_architecture_summary(root)

    assert result["status"] == "completed"
    assert result["read_only"] is True
    assert result["external_calls"] == 0
    assert result["commands_executed"] == 0
    assert set(result["source_files"]) == {
        "README.md",
        "docs/architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md",
    }
    assert any(source["path"] == "README.md" and source["start_line"] == 5 for source in result["sources"])
    assert "README.md:L5-L5" in result["output"]
    assert "The cockpit is presentation-only." in result["output"]
    assert sorted(path.name for path in root.iterdir()) == ["README.md", "docs"]


def test_architecture_summary_fails_closed_when_trusted_sections_are_missing(tmp_path):
    (tmp_path / "README.md").write_text("# DGM-MAT\n\n## Current role\n\nOnly one section.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Insufficient trusted architecture evidence"):
        build_architecture_summary(tmp_path)
