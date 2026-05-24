from pathlib import Path
from typing import Dict, Any, Optional
from core.import_fabric.repo_cloner import RepoCloner
from core.import_fabric.repo_classifier import RepoClassifier
from core.import_fabric.repo_indexer import RepoIndexer
from core.import_fabric.external_registry import ExternalRegistry
from core.import_fabric.repo_health import RepoHealth
from core.import_fabric.dependency_mapper import DependencyMapper
from core.observability.logger import dgm_logger

class ImportOrchestrator:
    """
    Orchestrates the entire import process.
    """
    def __init__(self, workspace: Path = Path("labs/external")):
        self.cloner = RepoCloner(workspace)
        self.classifier = RepoClassifier()
        self.indexer = RepoIndexer()
        self.registry = ExternalRegistry()
        self.health_checker = RepoHealth()
        self.dep_mapper = DependencyMapper()

    def run_import(self, repo_url: str, category_override: Optional[str] = None) -> Dict[str, Any]:
        name = repo_url.split("/")[-1].replace(".git", "")
        dgm_logger.info(f"Starting orchestration for {name}...")

        repo_path = self.cloner.clone(repo_url)
        if not repo_path:
            return {"status": "error", "message": "Cloning failed"}

        role = category_override or self.classifier.classify(repo_path)
        health = self.health_checker.check_health(repo_path)
        deps = self.dep_mapper.map_dependencies(repo_path)
        index = self.indexer.index(repo_path)

        metadata = {
            "name": name,
            "url": repo_url,
            "path": str(repo_path),
            "role": role,
            "health": health,
            "dependencies": deps,
            "status": "integrated"
        }

        self.registry.register_repo(name, metadata)
        dgm_logger.info(f"Import of {name} complete.")

        return metadata
