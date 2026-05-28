from typing import Dict, Any, Optional
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemStatus, EcosystemNode, EcosystemRole
from core.observability.logger import dgm_logger

class SafeImportSystem:
    def __init__(self, registry: Optional[EcosystemRegistry] = None):
        self.registry = registry or EcosystemRegistry()

    def process_import(self, repo_name: str, role: EcosystemRole = EcosystemRole.LABS) -> Dict[str, Any]:
        """
        Processes a new repository import through the safe pipeline.
        DISCOVERED -> LABS -> EVALUATION -> MANUAL_APPROVAL -> ACTIVE
        """
        node = self.registry.get_node(repo_name)

        if not node:
            # Start of pipeline
            dgm_logger.info(f"SafeImportSystem: Discovering new repo {repo_name}")
            node = EcosystemNode(
                name=repo_name,
                role=role,
                status=EcosystemStatus.DISCOVERED
            )
            self.registry.register_node(node)
            self.registry.save()
            return {"status": "success", "message": f"Repo {repo_name} discovered.", "current_state": node.status}

        # Transition logic
        if node.status == EcosystemStatus.DISCOVERED:
            node.status = EcosystemStatus.LABS
            self.registry.update_node(repo_name, status=node.status)
            return {"status": "success", "message": f"Repo {repo_name} moved to LABS.", "current_state": node.status}

        elif node.status == EcosystemStatus.LABS:
            node.status = EcosystemStatus.EVALUATION
            self.registry.update_node(repo_name, status=node.status)
            return {"status": "success", "message": f"Repo {repo_name} moved to EVALUATION.", "current_state": node.status}

        elif node.status == EcosystemStatus.EVALUATION:
            node.status = EcosystemStatus.MANUAL_APPROVAL
            self.registry.update_node(repo_name, status=node.status)
            return {"status": "success", "message": f"Repo {repo_name} awaiting MANUAL_APPROVAL.", "current_state": node.status}

        elif node.status == EcosystemStatus.MANUAL_APPROVAL:
            # In a real scenario, this would check for a user approval flag
            dgm_logger.info(f"SafeImportSystem: Repo {repo_name} requires manual approval to become ACTIVE.")
            return {"status": "pending", "message": f"Repo {repo_name} is awaiting manual approval.", "current_state": node.status}

        elif node.status == EcosystemStatus.ACTIVE:
            return {"status": "info", "message": f"Repo {repo_name} is already ACTIVE.", "current_state": node.status}

        return {"status": "error", "message": f"Repo {repo_name} is in an unknown state for the pipeline: {node.status}"}

    def approve_import(self, repo_name: str) -> Dict[str, Any]:
        """
        Manually approves an import, moving it from MANUAL_APPROVAL to ACTIVE.
        """
        node = self.registry.get_node(repo_name)
        if not node:
            return {"status": "error", "message": f"Repo {repo_name} not found."}

        if node.status == EcosystemStatus.MANUAL_APPROVAL:
            node.status = EcosystemStatus.ACTIVE
            self.registry.update_node(repo_name, status=node.status)
            dgm_logger.info(f"SafeImportSystem: Repo {repo_name} approved and is now ACTIVE.")
            return {"status": "success", "message": f"Repo {repo_name} is now ACTIVE.", "current_state": node.status}
        else:
            return {"status": "error", "message": f"Repo {repo_name} is not in MANUAL_APPROVAL state (current: {node.status})."}
