# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\organization\\test_ecosystem_discovery.py

from core.organization import CapabilityRequest, EcosystemDiscovery


def test_discovery_ranks_matching_lab(tmp_path):
    lab = tmp_path / "browser-lab"
    lab.mkdir()
    (lab / "SKILL.md").write_text(
        "# Browser automation\nplaywright browser scrolling\n",
        encoding="utf-8",
    )
    other = tmp_path / "voice-project"
    other.mkdir()
    (other / "README.md").write_text("# Voice tools\n", encoding="utf-8")

    request = CapabilityRequest(
        "cap:browser",
        "browser automation",
        "recover conversations",
        "mission:1",
        "agent:conversation-intelligence",
        required_skills=["browser", "playwright"],
    )
    report = EcosystemDiscovery([tmp_path]).discover(request)

    assert report.matches
    assert report.matches[0].candidate.source.name == "browser-lab"
    assert report.matches[0].candidate.source.source_type == "dgm_lab"
    assert report.matches[0].candidate.fit_score > 0.5


def test_discovery_reports_capability_overlap(tmp_path):
    for name in ("lab-a", "lab-b"):
        root = tmp_path / name
        root.mkdir()
        (root / "SKILL.md").write_text("# Browser\nplaywright\n", encoding="utf-8")

    request = CapabilityRequest(
        "cap:browser",
        "browser",
        "test overlap",
        "mission:1",
        "agent:hq",
        required_skills=["browser"],
    )
    report = EcosystemDiscovery([tmp_path]).discover(request)

    assert report.overlap_clusters
    assert report.overlap_clusters[0].source_ids == ["local:lab-a", "local:lab-b"]
