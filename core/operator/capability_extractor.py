from typing import Dict, Any, List
from pathlib import Path
from core.observability.logger import dgm_logger

class CapabilityExtractor:
    """
    Analyzes imported repositories and extracts useful capabilities.
    """
    def __init__(self, workspace_graph):
        self.workspace_graph = workspace_graph

    def analyze_repo(self, repo_path: Path) -> Dict[str, Any]:
        dgm_logger.info(f"CapabilityExtractor: Analyzing repository at {repo_path}")
        capabilities = {
            "name": repo_path.name,
            "patterns": self._detect_patterns(repo_path),
            "modules": self._identify_reusable_modules(repo_path)
        }

        # Link capabilities to the workspace graph
        self.workspace_graph.add_relationship(repo_path.name, "CapabilityGraph", "exports_capabilities")
        return capabilities

    def _detect_patterns(self, path: Path) -> List[str]:
        patterns = []
        name = path.name.lower()
        if "langgraph" in name: patterns.append("orchestration")
        if "crewai" in name: patterns.append("multi_agent")
        if "qdrant" in name: patterns.append("vector_memory")
        if "temporal" in name: patterns.append("durable_execution")
        return patterns

    def _identify_reusable_modules(self, path: Path) -> List[str]:
        # Logic to find public APIs or core logic files
        return [str(f.name) for f in path.glob("*.py") if not f.name.startswith("_")]
