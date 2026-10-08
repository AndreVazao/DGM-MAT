# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\organization\\test_capability_scout.py

from core.organization.capability_scout import CapabilityScout


def test_capability_scout_never_promotes(tmp_path):
    lab = tmp_path / "browser-lab"
    lab.mkdir()
    (lab / "SKILL.md").write_text(
        "# Browser\nplaywright browser automation\n",
        encoding="utf-8",
    )

    result = CapabilityScout([tmp_path]).discover(
        "browser automation",
        "recover browser conversations",
        required_skills=["browser", "playwright"],
    )

    assert result["agent_id"] == "agent:capability-scout"
    assert result["matches"][0]["name"] == "browser-lab"
    assert result["promotion"] == "not_performed"
    assert result["execution"] == "not_performed"
