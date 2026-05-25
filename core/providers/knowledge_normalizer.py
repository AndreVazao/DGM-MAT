import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.providers.models.conversation import Conversation

class ReusableKnowledge(BaseModel):
    knowledge_id: str
    topic: str
    content: str
    source_conversations: List[str]
    detected_projects: List[str]
    confidence_score: float
    last_updated: datetime = Field(default_factory=datetime.now)

class KnowledgeNormalizer:
    """
    Normalizes provider conversations, clusters them by project,
    and extracts reusable knowledge structures.
    """
    def __init__(self):
        self.storage = storage_manager
        self.knowledge_domain = "provider_knowledge"
        self.kb_filename = "project_knowledge_base.json"
        self.kb: Dict[str, ReusableKnowledge] = self._load_kb()

    def _load_kb(self) -> Dict[str, ReusableKnowledge]:
        content = self.storage.read_data(self.knowledge_domain, self.kb_filename)
        if content:
            try:
                data = json.loads(content)
                return {k: ReusableKnowledge(**v) for k, v in data.items()}
            except Exception as e:
                dgm_logger.error(f"KnowledgeNormalizer: Failed to load KB: {e}")
        return {}

    def _save_kb(self):
        data = {k: v.model_dump(mode="json") for k, v in self.kb.items()}
        self.storage.save_data(self.knowledge_domain, self.kb_filename, json.dumps(data, indent=2))

    def normalize_and_cluster(self, conversations: List[Conversation]):
        """Processes conversations to extract reusable knowledge."""
        dgm_logger.info(f"KnowledgeNormalizer: Normalizing {len(conversations)} conversations...")

        for convo in conversations:
            # 1. Clustering by detected projects
            projects = convo.detected_projects or ["general"]

            # 2. Extracting knowledge fragments (placeholder logic)
            # In a real scenario, this would use LLM summarization or keyword extraction
            # to identify recurring solutions or architecture patterns discussed.

            if "architecture" in convo.title.lower() or "implementation" in convo.title.lower():
                self._extract_from_convo(convo)

        self._save_kb()

    def _extract_from_convo(self, convo: Conversation):
        """Extracts specific knowledge fragments from a conversation."""
        knowledge_id = f"know_{convo.id[:8]}"

        # Simple extraction placeholder
        if knowledge_id not in self.kb:
            self.kb[knowledge_id] = ReusableKnowledge(
                knowledge_id=knowledge_id,
                topic=convo.title,
                content=f"Extracted architectural insights from {convo.provider} conversation.",
                source_conversations=[convo.id],
                detected_projects=convo.detected_projects,
                confidence_score=0.8
            )
        else:
            if convo.id not in self.kb[knowledge_id].source_conversations:
                self.kb[knowledge_id].source_conversations.append(convo.id)
                self.kb[knowledge_id].confidence_score = min(1.0, self.kb[knowledge_id].confidence_score + 0.05)

    def detect_contradictions(self) -> List[Dict[str, Any]]:
        """Detects contradictory solutions across different conversations."""
        # Placeholder for contradiction detection
        return []

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Returns a summary of the extracted knowledge."""
        return {
            "total_knowledge_fragments": len(self.kb),
            "top_topics": [k.topic for k in sorted(self.kb.values(), key=lambda x: x.confidence_score, reverse=True)[:5]],
            "project_coverage": self._get_project_coverage()
        }

    def _get_project_coverage(self) -> Dict[str, int]:
        coverage = {}
        for k in self.kb.values():
            for p in k.detected_projects:
                coverage[p] = coverage.get(p, 0) + 1
        return coverage

# Singleton instance
knowledge_normalizer = KnowledgeNormalizer()
