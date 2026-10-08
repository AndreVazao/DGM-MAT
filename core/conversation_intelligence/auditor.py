from __future__ import annotations

import ast
import re
from collections import defaultdict
from .models import AuditFinding, CodeArtifact, ConversationAudit, ConversationRecord

PROJECT_TERMS = {
    "DGM-MAT": ("dgm-mat", "god mode", "devops", "multi-agent", "multi agent"),
    "VAZAO-EVSE": ("evse", "charger", "charging station", "wallbox"),
    "PROVENTIL": ("proventil", "restaurant extraction", "video porteiro"),
    "AUTOMOTIVE": ("ecu", "engine swap", "car parts", "automotive"),
    "TRADING": ("sovereign trader", "freqtrade", "trading bot"),
    "BARIBUDOS": ("baribudos", "children's stories", "children stories"),
    "N8N": ("n8n", "workflow automation"),
}

class ConversationAuditor:
    def audit(self, conversation: ConversationRecord, artifacts: list[CodeArtifact]) -> ConversationAudit:
        text = f"{conversation.title}\n{conversation.content}".lower()
        scores = {project: sum(text.count(term) for term in terms) for project, terms in PROJECT_TERMS.items()}
        suggested_project = max(scores, key=scores.get) if max(scores.values(), default=0) else None
        findings: list[AuditFinding] = []
        for artifact in artifacts:
            if artifact.syntax_ok is False:
                findings.append(AuditFinding("error", "syntax", artifact.findings[0] if artifact.findings else "Syntax error", conversation.conversation_id, artifact.artifact_id, artifact.file_path))
            artifact.context_score = self._context_score(text, artifact)
            if artifact.context_score < 0.25:
                findings.append(AuditFinding("warning", "context-mismatch", "Code candidate has weak lexical alignment with the conversation context.", conversation.conversation_id, artifact.artifact_id, artifact.file_path))
            findings.extend(self._complexity_findings(conversation, artifact))
        return ConversationAudit(conversation=conversation, artifacts=artifacts, findings=findings, suggested_project=suggested_project, suggested_title=self._suggest_title(conversation, suggested_project))

    def _context_score(self, text: str, artifact: CodeArtifact) -> float:
        if not artifact.file_path: return 0.35
        tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9_-]{3,}", artifact.file_path)]
        if not tokens: return 0.35
        return min(1.0, sum(1 for token in tokens if token in text) / len(tokens))

    def _complexity_findings(self, conversation: ConversationRecord, artifact: CodeArtifact) -> list[AuditFinding]:
        findings = []
        if artifact.language == "python":
            try:
                tree = ast.parse(artifact.code)
                classes = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
                functions = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
                imports = sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
                if classes >= 4 and functions >= 12: findings.append(AuditFinding("warning", "possible-overengineering", f"Candidate contains {classes} classes and {functions} functions; review whether the abstraction level is justified.", conversation.conversation_id, artifact.artifact_id, artifact.file_path))
                if imports >= 15: findings.append(AuditFinding("warning", "dependency-density", f"Candidate has {imports} import statements; check for unnecessary coupling.", conversation.conversation_id, artifact.artifact_id, artifact.file_path))
            except SyntaxError: pass
        return findings

    @staticmethod
    def _suggest_title(conversation: ConversationRecord, project: str | None) -> str:
        title = re.sub(r"\\s+", " ", conversation.title).strip()
        if project and project.lower() not in title.lower(): return f"{project} - {title}"
        return title or "Imported conversation"

class CodeConsolidator:
    def consolidate_candidates(self, artifacts: list[CodeArtifact]) -> dict:
        groups: dict[str, list[CodeArtifact]] = defaultdict(list)
        for artifact in artifacts: groups[artifact.fingerprint].append(artifact)
        duplicate_groups = [items for items in groups.values() if len(items) > 1]
        return {"artifact_count": len(artifacts), "unique_count": len(groups), "duplicate_groups": [{"fingerprint": items[0].fingerprint, "artifacts": [a.artifact_id for a in items], "providers": sorted({a.provider for a in items}), "file_paths": sorted({a.file_path for a in items if a.file_path})} for items in duplicate_groups], "action": "review_and_consolidate"}
