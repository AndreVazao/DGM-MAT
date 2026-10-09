# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\provider_sync\\test_provider_cost_optimizer.py
from core.providers.performance.provider_cost_optimizer import ProviderCostOptimizer


def test_optimizer_prefers_local_first():
    assert ProviderCostOptimizer().optimize_cost("high") == "local-first"


def test_optimizer_never_selects_unverified_or_paid_provider():
    result = ProviderCostOptimizer().optimize_cost(
        "high",
        local_available=False,
        free_providers=[
            {"provider_id": "paid", "cost_profile": "paid", "billing_mode": "paid_api", "cost_verified": True, "quota_used": 0, "quota_limit": 10},
            {"provider_id": "unknown", "cost_profile": "free", "billing_mode": "free_tier", "cost_verified": False, "quota_used": 0, "quota_limit": 10},
        ],
    )
    assert result == "wait-for-free-capacity"


def test_optimizer_selects_only_verified_free_provider_with_quota():
    result = ProviderCostOptimizer().optimize_cost(
        "high",
        local_available=False,
        free_providers=[
            {"provider_id": "exhausted", "cost_profile": "free", "billing_mode": "free_tier", "cost_verified": True, "quota_used": 10, "quota_limit": 10},
            {"provider_id": "free-a", "cost_profile": "free", "billing_mode": "free_tier", "cost_verified": True, "quota_used": 1, "quota_limit": 10},
        ],
    )
    assert result == "free-a"


def test_optimizer_waits_when_no_free_capacity_is_verified():
    assert ProviderCostOptimizer().optimize_cost(
        "low", local_available=False, free_providers=()
    ) == "wait-for-free-capacity"
