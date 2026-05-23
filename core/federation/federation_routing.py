from core.federation.federation_models import FederationMessage

class FederationRouting:
    def resolve_target(self, message: FederationMessage) -> str:
        return message.target_ecosystem
