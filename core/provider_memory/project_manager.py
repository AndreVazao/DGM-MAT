import json
import time
from pathlib import Path
from typing import Dict, Any, List
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class ProjectManager:
    """
    Organizes provider conversations into logical projects and builds timelines.
    """
    def __init__(self):
        self.storage_path = storage_manager.get_path("provider_knowledge") / "projects"
        self._ensure_storage()

    def _ensure_storage(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def group_conversations(self, conversations: List[Dict[str, Any]]):
        """Groups conversations into projects based on metadata and content similarity."""
        # Simple grouping by 'project_name' or 'repo' if present in metadata
        projects: Dict[str, List[Dict[str, Any]]] = {}

        for conv in conversations:
            metadata = conv.get("metadata", {})
            project_id = metadata.get("project_id") or metadata.get("repo") or "unsorted"

            if project_id not in projects:
                projects[project_id] = []
            projects[project_id].append(conv)

        for project_id, con_list in projects.items():
            self._persist_project(project_id, con_list)

    def _persist_project(self, project_id: str, conversations: List[Dict[str, Any]]):
        project_file = self.storage_path / f"{project_id}.json"

        # Build timeline
        conversations.sort(key=lambda x: x.get("timestamp", 0))

        project_data = {
            "project_id": project_id,
            "last_updated": time.time(),
            "conversation_count": len(conversations),
            "timeline": [
                {
                    "id": c.get("id"),
                    "timestamp": c.get("timestamp"),
                    "summary": c.get("summary", "No summary")
                } for c in conversations
            ],
            "architecture_decisions": self._extract_decisions(conversations)
        }

        try:
            project_file.write_text(json.dumps(project_data, indent=2))
            dgm_logger.info(f"ProjectManager: Updated project {project_id}")
        except Exception as e:
            dgm_logger.error(f"ProjectManager: Failed to persist project {project_id}: {e}")

    def _extract_decisions(self, conversations: List[Dict[str, Any]]) -> List[str]:
        # Placeholder for AI-driven decision extraction
        return ["Initial architecture setup", "Transition to autonomous runtime"]

    def health(self) -> Dict[str, Any]:
        return {
            "projects_count": len(list(self.storage_path.glob("*.json")))
        }
