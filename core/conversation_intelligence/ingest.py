from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from .models import ConversationMessage, ConversationRecord


class ConversationIngestor:
    """Normalize exported/provider conversation data without mutating provider accounts."""

    def load_file(self, path: str | Path, provider: str | None = None) -> list[ConversationRecord]:
        source = Path(path)
        text = source.read_text(encoding="utf-8", errors="replace")
        provider_name = self.normalize_provider(provider or source.stem)
        if source.suffix.lower() == ".json":
            return self.from_json(text, provider_name, str(source))
        if source.suffix.lower() in {".html", ".htm"}:
            return self.from_html(text, provider_name, str(source))
        return [ConversationRecord(
            conversation_id=self._id(source.name, text),
            provider=provider_name,
            title=source.stem,
            content=text,
            source="file",
            metadata={"path": str(source)},
        )]

    def from_json(self, text: str, provider: str = "unknown", source: str = "json") -> list[ConversationRecord]:
        data: Any = json.loads(text)
        items = self._find_conversations(data)
        result: list[ConversationRecord] = []
        for index, item in enumerate(items):
            if isinstance(item, dict):
                title = str(item.get("title") or item.get("name") or f"Conversation {index + 1}")
                cid = str(item.get("id") or item.get("conversation_id") or self._id(f"{provider}-{index}", json.dumps(item, sort_keys=True)))
                content = self._flatten_text(item)
                result.append(ConversationRecord(
                    conversation_id=cid,
                    provider=self.normalize_provider(str(item.get("provider") or provider)),
                    title=title,
                    content=content,
                    source=source,
                    url=item.get("url"),
                    metadata={"raw_keys": sorted(item.keys())},
                    messages=self._extract_messages(item, cid, source),
                ))
        return result

    def from_html(self, text: str, provider: str = "unknown", source: str = "html") -> list[ConversationRecord]:
        cleaned = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", text, flags=re.I)
        title_match = re.search(r"<title[^>]*>(.*?)</title>", cleaned, re.I | re.S)
        title = html.unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else Path(source).stem
        content = html.unescape(re.sub(r"<[^>]+>", " ", cleaned))
        content = re.sub(r"\s+", " ", content).strip()
        return [ConversationRecord(
            conversation_id=self._id(source, content),
            provider=self.normalize_provider(provider),
            title=title or Path(source).stem,
            content=content,
            source=source,
            metadata={"format": "html"},
        )]

    def _extract_messages(self, item: dict[str, Any], conversation_id: str, source: str) -> list[ConversationMessage]:
        """Extract only explicit message arrays; never invent speaker attribution."""
        candidates: Any = item.get("messages")
        if isinstance(candidates, dict):
            candidates = candidates.get("messages") or candidates.get("items")
            if not isinstance(candidates, list):
                return []
        if not isinstance(candidates, list):
            mapping = item.get("mapping")
            if isinstance(mapping, dict):
                nodes = []
                for node_id, node in mapping.items():
                    if not isinstance(node, dict) or not isinstance(node.get("message"), dict):
                        continue
                    message = node["message"]
                    author = message.get("author") if isinstance(message.get("author"), dict) else {}
                    body = message.get("content", {})
                    nodes.append({
                        "id": message.get("id") or node_id,
                        "role": author.get("role") or "unknown",
                        "content": self._flatten_text(body),
                        "timestamp": message.get("create_time"),
                    })
                candidates = sorted(nodes, key=lambda x: (x.get("timestamp") is None, x.get("timestamp") or 0))
            else:
                return []

        result: list[ConversationMessage] = []
        for message in candidates:
            if not isinstance(message, dict):
                continue
            author = message.get("author") if isinstance(message.get("author"), dict) else {}
            role = str(message.get("role") or message.get("speaker") or message.get("sender") or author.get("role") or "unknown").strip().lower()
            body = message.get("content")
            if body is None:
                body = message.get("text", message.get("message", message.get("parts", "")))
            text = self._flatten_text(body).strip()
            if not text:
                continue
            timestamp = message.get("timestamp", message.get("create_time", message.get("created_at")))
            message_id = str(message.get("id") or message.get("message_id") or self._id(f"{conversation_id}:{len(result)}", text))
            result.append(ConversationMessage(
                message_id=message_id,
                role=role,
                content=text,
                sequence=len(result),
                timestamp=str(timestamp) if timestamp is not None else None,
                source_path=source,
                metadata={"raw_keys": sorted(message.keys())},
            ))
        return result

    def _find_conversations(self, data: Any) -> list[Any]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("conversations", "items", "sessions", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
            return [data]
        return []

    def _flatten_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "\n".join(self._flatten_text(v) for v in value)
        if isinstance(value, dict):
            preferred = ("content", "text", "message", "parts", "body", "prompt", "response")
            chunks = []
            for key in preferred:
                if key in value:
                    chunks.append(self._flatten_text(value[key]))
            if chunks:
                return "\n".join(chunks)
            return "\n".join(f"{k}: {self._flatten_text(v)}" for k, v in value.items())
        return str(value)

    @staticmethod
    def normalize_provider(value: str) -> str:
        normalized = value.lower().strip()
        aliases = {
            "chatgpt": "chatgpt", "openai": "chatgpt",
            "claude": "claude", "anthropic": "claude",
            "grok": "grok", "xai": "grok",
            "deepseek": "deepseek", "gemini": "gemini",
            "copilot": "copilot", "telescope": "telescope",
        }
        return aliases.get(normalized, "unknown")

    @staticmethod
    def _id(seed: str, content: str) -> str:
        import hashlib
        return hashlib.sha256(f"{seed}\n{content}".encode("utf-8")).hexdigest()[:24]
