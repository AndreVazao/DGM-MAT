import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class ArchitecturalPattern(BaseModel):
    pattern_id: str
    name: str
    description: str
    implementation_examples: List[str]
    detected_in: List[str] # Repo names
    reusability_score: float
    template_structure: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class PatternExtractor:
    """
    Identifies and extracts reusable logic, common architectural patterns,
    and generates internal templates.
    """
    def __init__(self):
        self.storage = storage_manager
        self.patterns_domain = "patterns"
        self.library_filename = "pattern_library.json"
        self.library: Dict[str, ArchitecturalPattern] = self._load_library()

    def _load_library(self) -> Dict[str, ArchitecturalPattern]:
        content = self.storage.read_data(self.patterns_domain, self.library_filename)
        if content:
            try:
                data = json.loads(content)
                return {k: ArchitecturalPattern(**v) for k, v in data.items()}
            except Exception as e:
                dgm_logger.error(f"PatternExtractor: Failed to load library: {e}")
        return {}

    def _save_library(self):
        data = {k: v.model_dump(mode="json") for k, v in self.library.items()}
        self.storage.save_data(self.patterns_domain, self.library_filename, json.dumps(data, indent=2))

    def scan_for_patterns(self, repo_name: str, repo_path: Path):
        """Scans a repository for reusable implementations and repeated logic."""
        dgm_logger.info(f"PatternExtractor: Scanning {repo_name} for reusable patterns...")

        # Placeholder for pattern detection logic
        # In a real scenario, this would use AST parsing or semantic analysis
        # to find common structures like specialized adapters or event handlers.

        discovered_patterns = [
            {"name": "AsyncProviderAdapter", "description": "Asynchronous adapter for external AI providers"},
            {"name": "PydanticEventSchema", "description": "Standardized event schema using Pydantic"}
        ]

        for p_data in discovered_patterns:
            self.register_pattern(
                name=p_data["name"],
                description=p_data["description"],
                repo_source=repo_name
            )

    def register_pattern(self, name: str, description: str, repo_source: str):
        """Registers or updates a pattern in the library."""
        pattern_id = name.lower().replace(" ", "_")

        if pattern_id in self.library:
            if repo_source not in self.library[pattern_id].detected_in:
                self.library[pattern_id].detected_in.append(repo_source)
                self.library[pattern_id].reusability_score = min(1.0, self.library[pattern_id].reusability_score + 0.1)
        else:
            self.library[pattern_id] = ArchitecturalPattern(
                pattern_id=pattern_id,
                name=name,
                description=description,
                implementation_examples=[],
                detected_in=[repo_source],
                reusability_score=0.5
            )

        self._save_library()
        dgm_logger.info(f"PatternExtractor: Registered pattern {name}")

    def generate_adapter_suggestion(self, source_repo: str, target_repo: str) -> Optional[str]:
        """Suggests a consolidation or a reusable adapter between two repos."""
        # Check if they share patterns
        shared = []
        for p in self.library.values():
            if source_repo in p.detected_in and target_repo in p.detected_in:
                shared.append(p.name)

        if shared:
            return f"Consolidate shared patterns ({', '.join(shared)}) into a core library adapter."
        return None

    def get_pattern_library_summary(self) -> Dict[str, Any]:
        """Returns a summary of the current pattern library."""
        return {
            "total_patterns": len(self.library),
            "highly_reusable": [p.name for p in self.library.values() if p.reusability_score > 0.8],
            "most_common": sorted(self.library.values(), key=lambda p: len(p.detected_in), reverse=True)[0].name if self.library else None
        }

# Singleton instance
pattern_extractor = PatternExtractor()
