import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.observability.logger import dgm_logger

class ObsidianConnector:
    """
    Deep Obsidian Integration - Phase 42.3-LITE.
    Transforms the vault into a cognitive brain with semantic indexing and bidirectional linking.
    """
    def __init__(self, vault_path: str = None):
        if not vault_path:
            if os.name == 'nt':
                self.vault_path = Path("C:/ProgramasGodMode/obsidian-vault")
            else:
                self.vault_path = Path("./storage/obsidian-vault")
        else:
            self.vault_path = Path(vault_path)

        self._ensure_structure()
        self.indexed_notes: List[Dict[str, Any]] = []

    def _ensure_structure(self):
        subdirs = ["missions", "architecture", "memory", "evolution", "context", "repos"]
        if not self.vault_path.exists():
            try:
                self.vault_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                dgm_logger.warning(f"ObsidianConnector: Could not create vault: {e}")
                return

        for subdir in subdirs:
            (self.vault_path / subdir).mkdir(parents=True, exist_ok=True)

    def index_vault(self) -> Dict[str, Any]:
        """Markdown indexing and semantic relationship discovery."""
        if not self.vault_path.exists():
            return {"status": "error", "message": "Vault not found"}

        self.indexed_notes = []
        try:
            for note in self.vault_path.rglob("*.md"):
                try:
                    content = note.read_text(encoding="utf-8")
                    links = self._extract_links(content)
                    self.indexed_notes.append({
                        "name": note.stem,
                        "path": str(note.relative_to(self.vault_path)),
                        "size": len(content),
                        "tags": list(set(re.findall(r"#[a-zA-Z0-9_\-/]+", content))),
                        "links": links,
                        "mtime": os.path.getmtime(note),
                        "snippet": content[:200]
                    })
                except Exception:
                    continue
        except (PermissionError, OSError):
            dgm_logger.error(f"ObsidianConnector: Permission denied during indexing.")

        return {
            "vault": str(self.vault_path),
            "total_notes": len(self.indexed_notes),
            "notes": self.indexed_notes
        }

    def _extract_links(self, content: str) -> List[str]:
        """Extracts [[WikiLinks]] from content."""
        return re.findall(r"\[\[(.*?)\]\]", content)

    def create_mission_note(self, mission_data: Dict[str, Any]):
        """Creates a mission note with bidirectional links to related components."""
        mission_id = mission_data.get("id", "unknown")
        title = mission_data.get("title", f"Mission {mission_id}")
        content = f"# {title}\n\n"
        content += f"**ID:** {mission_id}\n"
        content += f"**Status:** {mission_data.get('status', 'unknown')}\n"
        content += f"**Timestamp:** {datetime.now().isoformat()}\n\n"
        content += "## Objective\n"
        content += f"{mission_data.get('objective', 'No objective specified.')}\n\n"

        related = mission_data.get("related_notes", [])
        if related:
            content += "## Related Notes\n"
            for note in related:
                content += f"- [[{note}]]\n"

        self.export_to_markdown("missions", f"mission_{mission_id}", content)

    def sync_repo_to_vault(self, repo_stats: Dict[str, Any]):
        """Synchronizes repository technical data to the vault."""
        repo_name = repo_stats.get("name")
        if not repo_name:
            return

        content = f"# Repo: {repo_name}\n\n"
        content += f"**Path:** {repo_stats.get('path')}\n"
        content += f"**Stacks:** {', '.join(repo_stats.get('stacks', []))}\n"
        content += f"**Debt Score:** {repo_stats.get('debt_score', 0.0)}\n\n"
        content += "## Description\n"
        content += "Automatically indexed from DGM-MAT Cognitive Filesystem.\n\n"

        self.export_to_markdown("repos", f"repo_{repo_name}", content)

    def export_to_markdown(self, category: str, filename: str, content: str):
        target_dir = self.vault_path / category
        target_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith(".md"):
            filename += ".md"

        target_file = target_dir / filename
        try:
            target_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            dgm_logger.error(f"ObsidianConnector: Export failed: {e}")
            return False

# Singleton
obsidian_connector = ObsidianConnector()
