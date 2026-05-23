from typing import List
from core.federation.federation_models import EcosystemProfile

class EcosystemRegistry:
    def __init__(self):
        self.ecosystems = []

    def register(self, profile: EcosystemProfile):
        self.ecosystems.append(profile)

    def get_ecosystems(self) -> List[EcosystemProfile]:
        return self.ecosystems
