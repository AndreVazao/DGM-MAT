from typing import List, Dict, Optional
from core.federation.federation_models import EcosystemProfile, EcosystemStatus, TrustLevel

class EcosystemRegistry:
    def __init__(self):
        self.ecosystems: Dict[str, EcosystemProfile] = {}
        self._initialize_reserved_ecosystems()

    def _initialize_reserved_ecosystems(self):
        reserved = [
            {
                "id": "DGM-MAT-Cluster",
                "name": "Cluster",
                "specialization": ["distributed execution", "workload balancing", "node federation", "cognition mesh", "distributed orchestration"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Media",
                "name": "Media",
                "specialization": ["media ingestion", "image/video/audio processing", "transcription", "embeddings", "asset intelligence"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Studio",
                "name": "Studio",
                "specialization": ["cockpit studio", "UI/UX systems", "workspace orchestration", "visual orchestration", "operator tooling"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Marketplace",
                "name": "Marketplace",
                "specialization": ["plugins", "packages", "extensions", "templates", "shared ecosystem distribution"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Memory",
                "name": "Memory",
                "specialization": ["persistent cognition", "semantic memory", "graph storage", "temporal memory", "archival systems"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Runtime",
                "name": "Runtime",
                "specialization": ["runtime kernel", "execution engine", "process orchestration", "runtime services", "adaptive execution"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Orchestrator",
                "name": "Orchestrator",
                "specialization": ["orchestration intelligence", "routing", "scheduling", "governance coordination", "federation execution"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-Agents",
                "name": "Agents",
                "specialization": ["specialized agents", "agent lifecycle", "worker coordination", "multi-agent cognition", "agent specialization registry"],
                "status": EcosystemStatus.RESERVED
            },
            {
                "id": "DGM-MAT-OS",
                "name": "OS",
                "specialization": ["operating layer", "local system integration", "installer", "updater", "system services", "deployment/runtime integration"],
                "status": EcosystemStatus.RESERVED
            }
        ]

        # Add existing active satellites
        active = [
            {"id": "DGM-MAT-Mobile", "name": "Mobile", "specialization": ["mobile interface"], "status": EcosystemStatus.ACTIVE},
            {"id": "DGM-MAT-Plugins", "name": "Plugins", "specialization": ["plugin system"], "status": EcosystemStatus.ACTIVE},
            {"id": "DGM-MAT-Labs", "name": "Labs", "specialization": ["experimental research"], "status": EcosystemStatus.ACTIVE},
            {"id": "DGM-MAT-Connectors", "name": "Connectors", "specialization": ["external integration"], "status": EcosystemStatus.ACTIVE},
            {"id": "DGM-MAT-Providers", "name": "Providers", "specialization": ["llm providers"], "status": EcosystemStatus.ACTIVE},
            {"id": "DGM-MAT-Assets", "name": "Assets", "specialization": ["shared assets"], "status": EcosystemStatus.ACTIVE},
            {"id": "DGM-MAT-Deploy", "name": "Deploy", "specialization": ["deployment pipelines"], "status": EcosystemStatus.ACTIVE},
        ]

        for entry in reserved + active:
            profile = EcosystemProfile(
                id=entry["id"],
                name=entry["name"],
                specialization=entry["specialization"],
                status=entry["status"],
                trust_level=TrustLevel.VERIFIED if entry["status"] == EcosystemStatus.ACTIVE else TrustLevel.LOW
            )
            self.register(profile)

    def register(self, profile: EcosystemProfile):
        self.ecosystems[profile.id] = profile

    def get_ecosystems(self) -> List[EcosystemProfile]:
        return list(self.ecosystems.values())

    def get_profile(self, ecosystem_id: str) -> Optional[EcosystemProfile]:
        return self.ecosystems.get(ecosystem_id)
