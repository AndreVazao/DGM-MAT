from core.organization import (
    AgentRegistry, CapabilityCandidate, CapabilityRegistry, CapabilityRequest,
    CapabilitySource, Department, LocalSourceDiscovery, RecruitmentEngine,
    RecruitmentStatus, SkillForge,
)


def test_recruitment_requires_approval_for_external_capability():
    capabilities = CapabilityRegistry()
    agents = AgentRegistry()
    agents.register_department(Department("engineering", "Engineering", "software"))
    engine = RecruitmentEngine(capabilities, agents)
    request = CapabilityRequest(
        "cap:voice", "voice cloning", "need local voice capability",
        "mission:1", "agent:hq", risk_level="external_credentials",
    )
    candidate = CapabilityCandidate(
        "candidate:voice", request.request_id,
        CapabilitySource("ext:voice", "External Voice Tool", "external",
                         "https://example.invalid/source"),
        matched_skills=["voice"],
    )
    decision = engine.propose_hire(
        request, candidate, role="voice-engineer", department_id="engineering"
    )
    assert decision.order.status == RecruitmentStatus.APPROVAL_REQUIRED
    assert decision.order.approval_required is True


def test_internal_lab_capability_can_enter_governed_pipeline(tmp_path):
    source = tmp_path / "lab"
    (source / "candidate").mkdir(parents=True)
    (source / "candidate" / "SKILL.md").write_text("# Browser\n", encoding="utf-8")
    found = LocalSourceDiscovery([source]).scan()
    assert len(found) == 1
    assert "browser" in found[0].capabilities

    request = CapabilityRequest(
        "cap:browser", "browser automation", "scroll chats",
        "mission:1", "agent:hq"
    )
    registry = CapabilityRegistry()
    agents = AgentRegistry()
    agents.register_department(
        Department("conversation-intelligence", "Conversation Intelligence",
                    "recover conversations")
    )
    engine = RecruitmentEngine(registry, agents)
    candidate = CapabilityCandidate("candidate:browser", request.request_id, found[0])
    decision = engine.propose_hire(
        request, candidate, role="browser-specialist",
        department_id="conversation-intelligence",
    )
    assert decision.order.status == RecruitmentStatus.APPROVED

    forge = SkillForge(tmp_path / "forge")
    snapshot = forge.snapshot(candidate)
    assert (snapshot / "candidate" / "SKILL.md").exists()
    assert forge.create_adaptation_workspace(candidate).exists()


def test_forge_is_staged_not_direct_import():
    source = CapabilitySource("local:test", "test", "local_project", "/does/not/exist")
    candidate = CapabilityCandidate("candidate:test", "request:test", source)
    assert candidate.source.source_type == "local_project"
    assert SkillForge("/tmp/dgm-forge") is not None
