import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from core.ecosystem.ecosystem_models import EcosystemNode, EcosystemStatus, EcosystemRole, EcosystemState
from core.storage.storage_manager import storage_manager

class EcosystemRegistry:
    def __init__(self):
        self.state = EcosystemState()
        self.registry_path = storage_manager.get_path("federation", "ecosystem_registry.json")
        self.load()
        if not self.state.nodes:
            self._initialize_defaults()

    def _initialize_defaults(self):
        defaults = [
            ("DGM-MAT-OS", EcosystemRole.CORE, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Runtime", EcosystemRole.CORE, EcosystemStatus.RESERVED),
            ("DGM-MAT-Orchestrator", EcosystemRole.CORE, EcosystemStatus.RESERVED),
            ("DGM-MAT-Cluster", EcosystemRole.INFRA, EcosystemStatus.RESERVED),
            ("DGM-MAT-Memory", EcosystemRole.INFRA, EcosystemStatus.RESERVED),
            ("DGM-MAT-Studio", EcosystemRole.PRODUCT, EcosystemStatus.RESERVED),
            ("DGM-MAT-Marketplace", EcosystemRole.PRODUCT, EcosystemStatus.RESERVED),
            ("DGM-MAT-Media", EcosystemRole.DATA, EcosystemStatus.RESERVED),
            ("DGM-MAT-Agents", EcosystemRole.AGENTS, EcosystemStatus.RESERVED),
            ("DGM-MAT-Mobile", EcosystemRole.PRODUCT, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Plugins", EcosystemRole.INFRA, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Labs", EcosystemRole.EXPERIMENTAL, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Connectors", EcosystemRole.INFRA, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Providers", EcosystemRole.INFRA, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Assets", EcosystemRole.DATA, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Deploy", EcosystemRole.INFRA, EcosystemStatus.ACTIVE),
        ]

        for name, role, status in defaults:
            self.register_node(EcosystemNode(name=name, role=role, status=status))
        self.save()

    def register_node(self, node: EcosystemNode):
        self.state.nodes[node.name] = node
        self.state.last_updated = datetime.now()

    def get_node(self, name: str) -> Optional[EcosystemNode]:
        return self.state.nodes.get(name)

    def list_nodes(self) -> List[EcosystemNode]:
        return list(self.state.nodes.values())

    def update_node(self, name: str, **kwargs):
        if name in self.state.nodes:
            node = self.state.nodes[name]
            for key, value in kwargs.items():
                if hasattr(node, key):
                    setattr(node, key, value)
            node.last_sync = datetime.now()
            self.state.last_updated = datetime.now()
            self.save()

    def save(self):
        try:
            self.registry_path.write_text(self.state.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Error saving registry: {e}")

    def load(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                    self.state = EcosystemState(**data)
            except Exception as e:
                print(f"Error loading registry: {e}")
                self.state = EcosystemState()
