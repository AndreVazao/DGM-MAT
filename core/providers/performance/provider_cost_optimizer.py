class ProviderCostOptimizer:
    """
    Select a zero-cost route only; this component must never recommend paid APIs.

    Callers should try a usable local model first, then a verified free-tier
    provider with remaining quota. If neither is available, defer the task.
    """
    def optimize_cost(self, task_priority: str, *, local_available: bool = True, free_providers=()):
        # Priority affects scheduling elsewhere, never whether money may be spent.
        if local_available:
            return "local-first"
        for provider in free_providers:
            if not isinstance(provider, dict):
                continue
            if (
                provider.get("cost_profile") == "free"
                and provider.get("billing_mode") == "free_tier"
                and provider.get("cost_verified") is True
                and isinstance(provider.get("quota_used"), int)
                and not isinstance(provider.get("quota_used"), bool)
                and isinstance(provider.get("quota_limit"), int)
                and not isinstance(provider.get("quota_limit"), bool)
                and provider["quota_used"] >= 0
                and provider["quota_limit"] > 0
                and provider["quota_used"] < provider["quota_limit"]
            ):
                provider_id = provider.get("provider_id")
                if isinstance(provider_id, str) and provider_id.strip():
                    return provider_id.strip()
        return "wait-for-free-capacity"
