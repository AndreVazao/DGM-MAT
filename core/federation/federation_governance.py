from core.federation.federation_models import FederationMessage

class FederationGovernance:
    def is_allowed(self, message: FederationMessage) -> bool:
        # Check permissions and trust levels
        return True
