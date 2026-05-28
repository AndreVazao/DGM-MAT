import json
import os
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from core.ecosystem.ecosystem_models import EcosystemNode, EcosystemStatus, EcosystemRole, EcosystemState
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class EcosystemRegistry:
    def __init__(self):
        self.state = EcosystemState()
        self.registry_path = storage_manager.get_path("federation", "ecosystem_registry.json")
        self.protected_config_path = Path("config/protected_assets.yaml")
        self.protected_assets: Dict[str, Any] = self._load_protected_assets()
        self.load()
        self._initialize_defaults()
        self.register_ui_tars_placeholder()

    def _load_protected_assets(self) -> Dict[str, Any]:
        if self.protected_config_path.exists():
            try:
                with open(self.protected_config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                dgm_logger.error(f"EcosystemRegistry: Failed to load protected assets: {e}")
        return {}

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
            ("DGM-MAT-Labs", EcosystemRole.LABS, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Connectors", EcosystemRole.CONNECTORS, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Providers", EcosystemRole.PROVIDERS, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Assets", EcosystemRole.DATA, EcosystemStatus.ACTIVE),
            ("DGM-MAT-Deploy", EcosystemRole.INFRA, EcosystemStatus.ACTIVE),
        ]

        modified = False
        for name, role, status in defaults:
            if name not in self.state.nodes:
                self.register_node(EcosystemNode(name=name, role=role, status=status))
                modified = True

        if modified:
            self.save()

    def register_ui_tars_placeholder(self):
        if "UI-TARS" not in self.state.nodes:
            node = EcosystemNode(
                name="UI-TARS",
                role=EcosystemRole.OPERATORS,
                status=EcosystemStatus.DISCOVERED,
                priority="VERY_HIGH",
                destination="Operators",
                description="Placeholder for future UI-TARS ingestion."
            )
            self.register_node(node)
            self.save()
            dgm_logger.info("EcosystemRegistry: Registered UI-TARS placeholder.")

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
            dgm_logger.error(f"Error saving registry: {e}")

    def load(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                    self.state = EcosystemState(**data)
            except Exception as e:
                dgm_logger.error(f"Error loading registry: {e}")
                self.state = EcosystemState()

    def sync_filesystem(self, dry_run: bool = False):
        """Synchronizes the physical filesystem with the registry state."""
        from core.ecosystem.ecosystem_materializer import EcosystemMaterializer
        materializer = EcosystemMaterializer(self)
        return materializer.materialize_all(dry_run=dry_run)
