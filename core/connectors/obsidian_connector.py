import os
import json
from pathlib import Path
from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class ObsidianConnector:
    """
    Requirement 6: Obsidian Integration.
    Uses Obsidian as an external persistent cognition layer.
    """
    def __init__(self, vault_path: str = None):
        if not vault_path:
            # Default to canonical workspace
            self.vault_path = Path("C:/ProgramasGodMode/obsidian-vault")
        else:
            self.vault_path = Path(vault_path)

        if os.name == 'nt' and not self.vault_path.exists():
            try:
                self.vault_path.mkdir(parents=True, exist_ok=True)
                (self.vault_path / "missions").mkdir(parents=True, exist_ok=True)
                (self.vault_path / "architecture").mkdir(parents=True, exist_ok=True)
            except Exception as e:
                dgm_logger.warning(f"ObsidianConnector: Could not initialize vault: {e}")

    def index_vault(self) -> Dict[str, Any]:
        """Requirement 6: Markdown indexing and vault discovery."""
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
                        "mtime": os.path.getmtime(note)
                    })
                except Exception:
                    continue
        except (PermissionError, OSError):
            dgm_logger.error(f"ObsidianConnector: Permission denied during indexing.")

        return {
            "vault": str(self.vault_path),
            "total_notes": len(indexed_data),
            "notes": indexed_data[:100]
        }

    def export_to_markdown(self, category: str, filename: str, content: str):
        """Requirement 6: Mission export and architecture documentation generation."""
        target_dir = self.vault_path / category
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"{filename}.md"
        try:
            target_file.write_text(content, encoding="utf-8")
            dgm_logger.info(f"ObsidianConnector: Exported {filename} to {category}")
            return True
        except Exception as e:
            dgm_logger.error(f"ObsidianConnector: Export failed: {e}")
            return False

    def sync_notes(self):
        """Requirement 6: Bidirectional note sync (Placeholder for Git/File sync)."""
        dgm_logger.info(f"ObsidianConnector: Syncing notes in {self.vault_path}")
        return {"status": "success", "vault": str(self.vault_path)}

obsidian_connector = ObsidianConnector()
