import json
import os
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime

from core.observability.logger import dgm_logger

class MemoryConsolidationEngine:
    """
    Deduplicates and merges memories and execution histories.
    Ensures long-term architectural stability.
    """
    def __init__(self):
        self.memory_dir = Path(".runtime/provider_memory")
        self.archive_dir = Path(".runtime/memory_archive")
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def consolidate(self):
        """
        Runs the consolidation process.
        """
        dgm_logger.info("MemoryConsolidationEngine: Starting consolidation cycle...")

        # Ensure we only pick files, not directories
        memories = [p for p in self.memory_dir.glob("*.json") if p.is_file() and not p.name.startswith("consolidated_")]
        if not memories:
            dgm_logger.info("MemoryConsolidationEngine: No memories to consolidate.")
            return

        # 1. Group by similarity (basic grouping by provider and title keywords)
        groups = self._group_memories(memories)

        for group_key, file_paths in groups.items():
            if len(file_paths) > 1:
                self._merge_group(group_key, file_paths)
            else:
                dgm_logger.debug(f"MemoryConsolidationEngine: Memory {group_key} is unique.")

        dgm_logger.info("MemoryConsolidationEngine: Consolidation cycle complete.")

    def _group_memories(self, paths: List[Path]) -> Dict[str, List[Path]]:
        groups = {}
        for path in paths:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    # Use a combination of provider and a simplified title as the key
                    title = data.get("title", "unknown").lower()
                    provider = data.get("provider", "unknown")
                    # Simplified key: first 3 words of title
                    key = f"{provider}_{'_'.join(title.split()[:3])}"
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(path)
            except Exception as e:
                dgm_logger.error(f"MemoryConsolidationEngine: Failed to read {path}: {e}")
        return groups

    def _merge_group(self, group_key: str, paths: List[Path]):
        dgm_logger.info(f"MemoryConsolidationEngine: Merging {len(paths)} memories for {group_key}")

        merged_data = {
            "group_key": group_key,
            "consolidated_at": datetime.now().isoformat(),
            "source_files": [p.name for p in paths],
            "merged_content": []
        }

        for p in paths:
            try:
                with open(p, "r") as f:
                    merged_data["merged_content"].append(json.load(f))
                # Archive the original
                archive_path = self.archive_dir / p.name
                # If archive already exists, add timestamp
                if archive_path.exists():
                    archive_path = self.archive_dir / f"{datetime.now().strftime('%H%M%S')}_{p.name}"
                p.replace(archive_path)
            except Exception as e:
                dgm_logger.error(f"MemoryConsolidationEngine: Failed to merge/archive {p}: {e}")

        consolidated_path = self.memory_dir / f"consolidated_{group_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(consolidated_path, "w") as f:
            json.dump(merged_data, f, indent=2)

        dgm_logger.info(f"MemoryConsolidationEngine: Created consolidated memory at {consolidated_path}")
