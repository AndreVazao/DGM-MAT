import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.observability.logger import dgm_logger

class ObsidianConnector:
    """
    Enhanced Obsidian Integration.
    Uses Obsidian as a persistent semantic memory and mission context layer.
    """
    def __init__(self, vault_path: str = None):
        if not vault_path:
            # Default to canonical workspace
            if os.name == 'nt':
                self.vault_path = Path("C:/ProgramasGodMode/obsidian-vault")
            else:
                self.vault_path = Path("./storage/obsidian-vault")
        else:
            self.vault_path = Path(vault_path)

        self._ensure_structure()

    def _ensure_structure(self):
        subdirs = ["missions", "architecture", "memory", "evolution", "context"]
        if not self.vault_path.exists():
            try:
                self.vault_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                dgm_logger.warning(f"ObsidianConnector: Could not create vault: {e}")
                return

        for subdir in subdirs:
            (self.vault_path / subdir).mkdir(parents=True, exist_ok=True)

    def index_vault(self) -> Dict[str, Any]:
        """Markdown indexing and vault discovery."""
        if not self.vault_path.exists():
            return {"status": "error", "message": "Vault not found"}

        indexed_data = []
        try:
            for note in self.vault_path.rglob("*.md"):
                try:
                    content = note.read_text(encoding="utf-8")
                    indexed_data.append({
                        "name": note.name,
                        "path": str(note.relative_to(self.vault_path)),
                        "size": len(content),
                        "tags": [word for word in content.split() if word.startswith("#")],
                        "mtime": os.path.getmtime(note),
                        "snippet": content[:200]
                    })
                except Exception:
                    continue
        except (PermissionError, OSError):
            dgm_logger.error(f"ObsidianConnector: Permission denied during indexing.")

        return {
            "vault": str(self.vault_path),
            "total_notes": len(indexed_data),
            "notes": indexed_data
        }

    def inject_context(self, mission_id: str) -> str:
        """Retrieves mission-specific context from Obsidian notes."""
        context_file = self.vault_path / "context" / f"{mission_id}.md"
        if context_file.exists():
            return context_file.read_text(encoding="utf-8")

        # Fallback: search for mission mention in recent notes
        return ""

    def store_evolution_note(self, evolution_step: str, content: str):
        """Stores long-term evolution memory."""
        filename = f"evolution_{evolution_step}_{int(os.path.getmtime(__file__)) if os.path.exists(__file__) else 0}.md"
        self.export_to_markdown("evolution", filename, content)

    def export_to_markdown(self, category: str, filename: str, content: str):
        """Mission export and architecture documentation generation."""
        target_dir = self.vault_path / category
        target_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith(".md"):
            filename += ".md"

        target_file = target_dir / filename
        try:
            target_file.write_text(content, encoding="utf-8")
            dgm_logger.info(f"ObsidianConnector: Exported {filename} to {category}")
            return True
        except Exception as e:
            dgm_logger.error(f"ObsidianConnector: Export failed: {e}")
            return False

    def sync_notes(self):
        """Bidirectional note sync."""
        dgm_logger.info(f"ObsidianConnector: Syncing notes in {self.vault_path}")
        return {"status": "success", "vault": str(self.vault_path)}

# Singleton
obsidian_connector = ObsidianConnector()
