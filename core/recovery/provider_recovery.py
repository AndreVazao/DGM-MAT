from core.observability.logger import dgm_logger


class ProviderRecovery:
    def recover_provider(self, provider_id: str) -> bool:
        """Return False until provider recovery is actually implemented and verified.

        Logging an intention to restore a session is not a recovery action.
        Callers must not record success until a concrete adapter/session check
        proves that the provider is operational again.
        """
        dgm_logger.warning(
            "Provider Recovery unavailable for %s: no verified recovery action is implemented.",
            provider_id,
        )
        return False
