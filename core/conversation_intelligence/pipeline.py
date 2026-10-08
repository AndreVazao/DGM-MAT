from __future__ import annotations
from pathlib import Path
from typing import Iterable
from .auditor import CodeConsolidator, ConversationAuditor
from .code_extractor import CodeExtractor
from .ingest import ConversationIngestor
from .models import ConversationAudit

class ConversationIntelligencePipeline:
    def __init__(self) -> None:
        self.ingestor = ConversationIngestor(); self.extractor = CodeExtractor(); self.auditor = ConversationAuditor(); self.consolidator = CodeConsolidator()
    def ingest_file(self, path: str | Path, provider: str | None = None) -> list[ConversationAudit]:
        conversations = self.ingestor.load_file(path, provider)
        return [self.auditor.audit(c, self.extractor.extract(c)) for c in conversations]
    def consolidate(self, audits: Iterable[ConversationAudit]) -> dict:
        return self.consolidator.consolidate_candidates([x for a in audits for x in a.artifacts])
    def summarize(self, audits: Iterable[ConversationAudit]) -> dict:
        audits = list(audits)
        return {"conversation_count": len(audits), "artifact_count": sum(len(a.artifacts) for a in audits), "projects": sorted({a.suggested_project for a in audits if a.suggested_project}), "errors": sum(1 for a in audits for f in a.findings if f.severity == "error"), "warnings": sum(1 for a in audits for f in a.findings if f.severity == "warning")}
