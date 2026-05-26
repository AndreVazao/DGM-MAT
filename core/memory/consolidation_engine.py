import json
import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime
from core.observability.logger import dgm_logger
from core.storage.storage_manager import storage_manager

class MemoryConsolidationEngine:
    """
    Deduplicates and merges memories and execution histories.
    Ensures long-term architectural stability.
    """
    def __init__(self):
        self.memory_dir = storage_manager.get_path("memory")
        self.archive_dir = storage_manager.get_path("temp") / "memory_archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def consolidate(self):
        dgm_logger.info("MemoryConsolidationEngine: Starting consolidation cycle...")
        memories = [p for p in self.memory_dir.glob("*.json") if p.is_file() and not p.name.startswith("consolidated_")]
        if not memories:
            dgm_logger.info("MemoryConsolidationEngine: No memories to consolidate.")
            return

        # 1. Group by semantic similarity (clustering)
        groups = self._group_memories_semantically(memories)

        for group_key, file_paths in groups.items():
            if len(file_paths) > 1:
                self._merge_group(group_key, file_paths)
            else:
                dgm_logger.debug(f"MemoryConsolidationEngine: Memory {group_key} is unique.")

        dgm_logger.info("MemoryConsolidationEngine: Consolidation cycle complete.")

    def _group_memories_semantically(self, paths: List[Path]) -> Dict[str, List[Path]]:
        """Performs semantic clustering on memories to identify duplicates."""
        groups = {}
        for path in paths:
            try:
                # Use ast.literal_eval for safety with the string-formatted dicts from MemoryEngine
                content_str = path.read_text(encoding="utf-8")
                data = ast.literal_eval(content_str)

                # Basic semantic clustering logic
                concept = data.get("concept", data.get("title", "unknown")).lower()
                # Simplified: group by first 5 characters of first 3 words
                cluster_key = "_".join([w[:5] for w in concept.split()[:3]])
                if cluster_key not in groups:
                    groups[cluster_key] = []
                groups[cluster_key].append(path)
            except Exception as e:
                dgm_logger.error(f"MemoryConsolidationEngine: Failed to read {path}: {e}")
        return groups

    def _merge_group(self, group_key: str, paths: List[Path]):
        dgm_logger.info(f"MemoryConsolidationEngine: Merging {len(paths)} memories into semantic cluster: {group_key}")

        merged_data = {
            "cluster_key": group_key,
            "consolidated_at": datetime.now().isoformat(),
            "source_files": [p.name for p in paths],
            "merged_content": []
        }

        for p in paths:
            try:
                content_str = p.read_text(encoding="utf-8")
                merged_data["merged_content"].append(ast.literal_eval(content_str))

                archive_path = self.archive_dir / p.name
                if archive_path.exists():
                    archive_path = self.archive_dir / f"{datetime.now().strftime('%H%M%S')}_{p.name}"
                p.replace(archive_path)
            except Exception as e:
                dgm_logger.error(f"MemoryConsolidationEngine: Failed to merge {p}: {e}")

        consolidated_path = self.memory_dir / f"consolidated_cluster_{group_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(consolidated_path, "w") as f:
            json.dump(merged_data, f, indent=2)

    def extract_strategic_memory(self, consolidated_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []

    def rank_importance(self, memory: Dict[str, Any]) -> float:
        return 0.5
