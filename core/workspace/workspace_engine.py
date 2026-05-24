from typing import List, Dict, Any
from pathlib import Path
from core.observability.logger import dgm_logger
from core.workspace.workspace_graph import WorkspaceGraph
from core.workspace.project_identity import ProjectIdentity
from core.workspace.semantic_project_mapper import SemanticProjectMapper

class WorkspaceEngine:
    """
    Orchestrates workspace cognition and project understanding.
    """
    def __init__(self):
        self.graph = WorkspaceGraph()
        self.mapper = SemanticProjectMapper()
        self.projects = {}

    def scan_workspace(self, root_path: str):
        dgm_logger.info(f"WorkspaceEngine: Scanning workspace at {root_path}")
        root = Path(root_path)
        for item in root.iterdir():
            if item.is_dir():
                identity = ProjectIdentity.identify(item)
                self.projects[item.name] = identity
                self.graph.add_project(identity)

        self.mapper.map_relationships(self.projects, self.graph)
        dgm_logger.info(f"WorkspaceEngine: Identified {len(self.projects)} projects.")

    def get_project_context(self, project_name: str) -> Dict[str, Any]:
        return self.graph.get_context(project_name)
