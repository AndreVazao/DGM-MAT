import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.observability.logger import dgm_logger
from core.autonomy.task_generator import TaskGenerator

class ConversationIngestionEngine:
    """
    Ingests local conversation exports from ChatGPT, Claude, and Gemini.
    Extracts actionable knowledge and tasks.
    """
    def __init__(self, task_generator: Optional[TaskGenerator] = None):
        self.task_generator = task_generator or TaskGenerator()
        self.memory_dir = Path(".runtime/provider_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def ingest_export(self, export_path: str, provider: str):
        """
        Parses a provider export file and extracts knowledge/tasks.
        """
        path = Path(export_path)
        if not path.exists():
            dgm_logger.error(f"ConversationIngestionEngine: Export path {export_path} does not exist.")
            return

        dgm_logger.info(f"ConversationIngestionEngine: Ingesting {provider} export from {export_path}")

        if provider.lower() == "chatgpt":
            self._parse_chatgpt(path)
        elif provider.lower() == "claude":
            self._parse_claude(path)
        else:
            dgm_logger.warning(f"ConversationIngestionEngine: Provider {provider} not supported yet.")

    def _parse_chatgpt(self, path: Path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for convo in data:
                    title = convo.get("title", "Untitled Conversation")
                    self._process_conversation(title, convo, "chatgpt")
        except Exception as e:
            dgm_logger.error(f"ConversationIngestionEngine: Failed to parse ChatGPT export: {e}")

    def _parse_claude(self, path: Path):
        # Implementation for Claude's JSON/CSV format
        pass

    def _process_conversation(self, title: str, data: Dict[str, Any], provider: str):
        # Simple extraction of tasks based on keywords
        messages = self._extract_messages(data, provider)
        for msg in messages:
            content = msg.get("content", "").lower()
            if "todo:" in content or "implement:" in content:
                self.task_generator.create_task(
                    title=f"Task from {provider}: {title[:30]}...",
                    description=msg.get("content", ""),
                    priority=40,
                    origin="provider_sync",
                    metadata={"provider": provider, "original_convo": title}
                )

        # Persist a summary to memory
        self._persist_memory_summary(title, messages, provider)

    def _extract_messages(self, data: Dict[str, Any], provider: str) -> List[Dict[str, str]]:
        messages = []
        if provider == "chatgpt":
            mapping = data.get("mapping", {})
            for node_id, node in mapping.items():
                message = node.get("message")
                if message and message.get("author", {}).get("role") == "assistant":
                    content_parts = message.get("content", {}).get("parts", [])
                    content = "".join([str(p) for p in content_parts if isinstance(p, str)])
                    if content:
                        messages.append({"role": "assistant", "content": content})
        return messages

    def _persist_memory_summary(self, title: str, messages: List[Dict[str, str]], provider: str):
        safe_title = "".join([c for c in title if c.isalnum() or c in " _-"]).strip()[:50]
        filename = f"mem_{provider}_{safe_title}_{datetime.now().strftime('%Y%m%d')}.json"
        memory_path = self.memory_dir / filename

        summary = {
            "title": title,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "preview": messages[0]["content"][:200] if messages else ""
        }

        with open(memory_path, "w") as f:
            json.dump(summary, f, indent=2)
