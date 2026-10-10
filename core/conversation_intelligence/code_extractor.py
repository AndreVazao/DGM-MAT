from __future__ import annotations

import ast
import hashlib
import re

from .models import ArtifactProvenance, CodeArtifact, ConversationRecord

FENCE_RE = re.compile(r"```([A-Za-z0-9_+#.-]*)\s*\n([\s\S]*?)```", re.MULTILINE)
FILE_RE = re.compile(r"(?://|#|<!--)\s*FILE:\s*([^\n>]+)", re.IGNORECASE)

class CodeExtractor:
    """Extract code candidates from conversation text, preserving source context."""

    def extract(self, conversation: ConversationRecord) -> list[CodeArtifact]:
        artifacts: list[CodeArtifact] = []
        matches = list(FENCE_RE.finditer(conversation.content))
        for index, match in enumerate(matches):
            language = self._language(match.group(1))
            code = match.group(2).strip("\n")
            if not self._looks_like_code(language, code):
                continue
            before = conversation.content[max(0, match.start() - 1000):match.start()]
            file_path = self._file_marker(before)
            artifact = CodeArtifact(
                artifact_id=hashlib.sha256(f"{conversation.conversation_id}:{index}:{code}".encode()).hexdigest()[:20],
                conversation_id=conversation.conversation_id,
                provider=conversation.provider,
                language=language,
                code=code,
                file_path=file_path,
                source_marker="markdown_fence",
                fingerprint=self.fingerprint(code),
                provenance=ArtifactProvenance(
                    artifact_id=hashlib.sha256(f"{conversation.conversation_id}:{index}:{code}".encode()).hexdigest()[:20],
                    conversation_id=conversation.conversation_id,
                    source_provider=conversation.provider,
                    source_url=conversation.url,
                    source_path=conversation.source or conversation.metadata.get("path"),
                    source_fingerprint=self.fingerprint(code),
                ),
            )
            self._validate_python(artifact)
            artifacts.append(artifact)
        return artifacts

    def _validate_python(self, artifact: CodeArtifact) -> None:
        if artifact.language in {"python", "py"}:
            try:
                ast.parse(artifact.code)
                artifact.syntax_ok = True
            except SyntaxError as exc:
                artifact.syntax_ok = False
                artifact.findings.append(f"Python syntax error: {exc.msg} at line {exc.lineno}")

    @staticmethod
    def fingerprint(code: str) -> str:
        normalized = re.sub(r"\s+", " ", code).strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _language(value: str) -> str:
        value = value.lower().strip()
        return {
            "py": "python", "python": "python",
            "js": "javascript", "javascript": "javascript",
            "ts": "typescript", "typescript": "typescript",
            "tsx": "tsx", "jsx": "jsx",
            "json": "json", "yaml": "yaml", "yml": "yaml",
            "ps1": "powershell", "powershell": "powershell",
            "sh": "shell", "bash": "shell", "sql": "sql",
        }.get(value, value or "unknown")

    @staticmethod
    def _file_marker(text: str) -> str | None:
        match = FILE_RE.findall(text)
        return match[-1].strip() if match else None

    @staticmethod
    def _looks_like_code(language: str, code: str) -> bool:
        if len(code.strip()) < 8:
            return False
        if language in {"text", "markdown", "md"}:
            return False
        signals = ("def ", "class ", "import ", "from ", "function ", "const ", "let ", "SELECT ", "{", "=>", "if ", "for ")
        return language not in {"unknown", ""} or any(signal in code for signal in signals)