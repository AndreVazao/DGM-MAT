import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemNode

class RepoFederationMetadata(BaseModel):
    repo_name: str
    classification: str
    overlap_score: float = 0.0
    usefulness_score: float = 0.0
    last_analyzed: datetime = Field(default_factory=datetime.now)
    status: str = "active"
    strategic_value: str = "medium" # high, medium, low
    compatibility_score: float = 1.0

class RepoFederationIndex:
    """
    Maintains a global index of all imported and internal repositories.
    Handles overlap detection, usefulness ranking, and strategic classification.
    """
    def __init__(self, registry: Optional[EcosystemRegistry] = None):
        self.registry = registry or EcosystemRegistry()
        self.storage = storage_manager
        self.index_filename = "repo_federation_index.json"
        self.index: Dict[str, RepoFederationMetadata] = self._load_index()

    def _load_index(self) -> Dict[str, RepoFederationMetadata]:
        content = self.storage.read_data("federation", self.index_filename)
        if content:
            try:
                data = json.loads(content)
                return {k: RepoFederationMetadata(**v) for k, v in data.items()}
            except Exception as e:
                dgm_logger.error(f"RepoFederationIndex: Failed to load index: {e}")
        return {}

    def _save_index(self):
        data = {k: v.model_dump(mode="json") for k, v in self.index.items()}
        self.storage.save_data("federation", self.index_filename, json.dumps(data, indent=2))

    def register_repo(self, repo_name: str, classification: str, metadata: Dict[str, Any] = None):
        """Registers or updates a repository in the federation index."""
        if repo_name not in self.index:
            self.index[repo_name] = RepoFederationMetadata(
                repo_name=repo_name,
                classification=classification
            )
        else:
            self.index[repo_name].classification = classification
            self.index[repo_name].last_analyzed = datetime.now()

        if metadata:
            # Update scores if provided
            self.index[repo_name].overlap_score = metadata.get("overlap_score", self.index[repo_name].overlap_score)
            self.index[repo_name].usefulness_score = metadata.get("usefulness_score", self.index[repo_name].usefulness_score)
            self.index[repo_name].strategic_value = metadata.get("strategic_value", self.index[repo_name].strategic_value)

        self._save_index()
        dgm_logger.info(f"RepoFederationIndex: Registered/Updated repo {repo_name}")

    def detect_overlaps(self):
        """Detects functional overlap between repositories in the federation."""
        dgm_logger.info("RepoFederationIndex: Running overlap detection...")
        for repo_a in self.index.values():
            for repo_b in self.index.values():
                if repo_a.repo_name == repo_b.repo_name:
                    continue
                if repo_a.classification == repo_b.classification:
                    repo_a.overlap_score = min(1.0, repo_a.overlap_score + 0.1)
        self._save_index()

    def rank_usefulness(self):
        """Ranks repositories based on their strategic utility and activity."""
        dgm_logger.info("RepoFederationIndex: Ranking repository usefulness...")
        for repo in self.index.values():
            base_score = 0.5
            if repo.strategic_value == "high":
                base_score += 0.3
            if repo.overlap_score < 0.2:
                base_score += 0.2
            repo.usefulness_score = min(1.0, base_score)
        self._save_index()

    def get_strategic_imports(self) -> List[str]:
        """Identifies missing but strategically important imports."""
        return ["OpenClaw", "LangGraph", "DSPy"]

    def get_dead_imports(self) -> List[str]:
        """Identifies repositories that are no longer useful or have 100% overlap."""
        return [name for name, repo in self.index.items() if repo.usefulness_score < 0.2 or repo.overlap_score > 0.9]

    def recommend_adapters(self, repo_name: str) -> List[str]:
        """Suggests adapters needed for a repository based on its classification and overlaps."""
        if repo_name not in self.index:
            return []

        repo = self.index[repo_name]
        recommendations = []
        if repo.overlap_score > 0.5:
            recommendations.append(f"Standardization adapter for {repo.classification}")
        if repo.compatibility_score < 0.7:
            recommendations.append("Protocol bridge adapter")

        return recommendations

    def get_federation_summary(self) -> Dict[str, Any]:
        """Returns a high-level summary of the repository federation."""
        return {
            "total_repos": len(self.index),
            "classifications": self._get_classification_distribution(),
            "high_value_repos": [name for name, repo in self.index.items() if repo.strategic_value == "high"],
            "average_usefulness": sum(r.usefulness_score for r in self.index.values()) / len(self.index) if self.index else 0
        }

    def _get_classification_distribution(self) -> Dict[str, int]:
        dist = {}
        for repo in self.index.values():
            dist[repo.classification] = dist.get(repo.classification, 0) + 1
        return dist

# Singleton instance
repo_federation = RepoFederationIndex()
