import pytest

from core.self_evolution.patch_candidate_generator import PatchCandidateGenerator
from core.self_evolution.safety_validator import SafetyValidator
from core.self_evolution.sandbox_runner import SandboxRunner
from core.self_evolution.evolution_engine import EvolutionEngine


def test_patch_generator_never_labels_placeholder_as_a_real_candidate():
    patch = PatchCandidateGenerator().generate_patch("core.autonomy")

    assert patch["status"] == "NOT_IMPLEMENTED"
    assert patch["diff"] is None
    assert patch["risk_score"] >= 50
    assert not SafetyValidator().validate(patch)


def test_safety_validator_rejects_simulated_diff():
    patch = {
        "module": "core.autonomy",
        "diff": "+++ simulated_diff",
        "risk_score": 15,
    }

    assert SafetyValidator().validate(patch) is False


def test_safety_validator_rejects_protected_targets_even_with_a_diff():
    patch = {
        "module": "core/governance/policy.py",
        "diff": (
            "diff --git a/core/governance/policy.py b/core/governance/policy.py\n"
            "--- a/core/governance/policy.py\n"
            "+++ b/core/governance/policy.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        ),
        "risk_score": 10,
    }

    assert SafetyValidator().validate(patch) is False


@pytest.mark.asyncio
async def test_sandbox_never_reports_simulated_success():
    patch = {
        "module": "core/example.py",
        "diff": (
            "diff --git a/core/example.py b/core/example.py\n"
            "--- a/core/example.py\n"
            "+++ b/core/example.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        ),
        "risk_score": 10,
    }

    assert await SandboxRunner().run(patch) is False


@pytest.mark.asyncio
async def test_evolution_engine_does_not_offer_placeholder_for_promotion():
    candidate = await EvolutionEngine().propose_evolution("core.autonomy")

    assert candidate is None
