import json
import datetime
from typing import Dict, Any, List, Optional
from core.memory.engine import MemoryEngine

class PromptGenome:
    def __init__(self, memory_engine: MemoryEngine):
        self.memory = memory_engine
        self.category = "prompt_library"

    def store_prompt(self, prompt_data: Dict[str, Any]):
        """Store a prompt with its metadata and success status."""
        current_library = self.memory.get_latest(self.category).get("data", {"prompts": []})

        prompt_entry = {
            "id": prompt_data.get("id"),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "prompt": prompt_data.get("prompt"),
            "provider": prompt_data.get("provider"),
            "gap_category": prompt_data.get("gap_category"),
            "success": prompt_data.get("success", False),
            "response_quality": prompt_data.get("response_quality", 0.0),
            "usage_count": 1
        }

        # Check if already exists to update
        existing = next((p for p in current_library["prompts"] if p["id"] == prompt_entry["id"]), None)
        if existing:
            existing.update(prompt_entry)
            existing["usage_count"] += 1
        else:
            current_library["prompts"].append(prompt_entry)

        self.memory.save_snapshot(self.category, current_library)

    def get_template(self, gap_category: str) -> Optional[str]:
        """Retrieve the best performing prompt for a category."""
        library = self.memory.get_latest(self.category).get("data", {"prompts": []})
        category_prompts = [p for p in library["prompts"] if p["gap_category"] == gap_category and p["success"]]

        if not category_prompts:
            return None

        # Return the one with highest quality
        best = max(category_prompts, key=lambda x: x["response_quality"])
        return best["prompt"]

    def list_all(self) -> List[Dict[str, Any]]:
        return self.memory.get_latest(self.category).get("data", {"prompts": []})["prompts"]
