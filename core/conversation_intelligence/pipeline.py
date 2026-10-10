from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .auditor import CodeConsolidator, ConversationAuditor
from .code_extractor import CodeExtractor
from .ingest import ConversationIngestor
from .models import ConversationAudit
from .progress_store import ConversationProgressStore


class ConversationIntelligencePipeline:
    def __init__(self, progress_store_path: str | Path | None = None) -> None:
        self.ingestor = ConversationIngestor()
        self.extractor = CodeExtractor()
        self.auditor = ConversationAuditor()
        self.consolidator = CodeConsolidator()
        self.progress_store = ConversationProgressStore(progress_store_path) if progress_store_path else None

    def ingest_file(self, path: str | Path, provider: str | None = None) -> list[ConversationAudit]:
        source_path = Path(path)
        conversations = self.ingestor.load_file(source_path, provider)
        audits: list[ConversationAudit] = []
        source_provider = self.ingestor.normalize_provider(provider or source_path.stem)
        source_key = str(source_path.resolve())
        source_fingerprint = self.progress_store.fingerprint(source_path.read_bytes()) if self.progress_store else None
        if self.progress_store:
            self.progress_store.record_source(
                source_provider, source_key, source_fingerprint or "", "partial",
                discovered_count=len(conversations), imported_count=0,
                checkpoint=None,
            )

        for conversation in conversations:
            if self.progress_store:
                stable_content = json.dumps({
                    "title": conversation.title,
                    "content": conversation.content,
                    "url": conversation.url,
                    "messages": [
                        {
                            "id": message.message_id,
                            "role": message.role,
                            "content": message.content,
                            "sequence": message.sequence,
                            "timestamp": message.timestamp,
                        }
                        for message in conversation.messages
                    ],
                }, ensure_ascii=False, sort_keys=True)
                fingerprint = self.progress_store.fingerprint(stable_content)
                if not self.progress_store.should_process(conversation.provider, conversation.conversation_id, fingerprint):
                    continue
                self.progress_store.record_conversation(
                    conversation.provider, conversation.conversation_id, fingerprint,
                    conversation.title, status="processing",
                )

            try:
                audit = self.auditor.audit(conversation, self.extractor.extract(conversation))
                audits.append(audit)
                if self.progress_store:
                    self.progress_store.record_conversation(
                        conversation.provider, conversation.conversation_id, fingerprint,
                        conversation.title, status="complete",
                        result={
                            "artifact_count": len(audit.artifacts),
                            "finding_count": len(audit.findings),
                            "artifact_fingerprints": [artifact.fingerprint for artifact in audit.artifacts],
                        },
                    )
            except Exception as exc:
                if self.progress_store:
                    self.progress_store.record_conversation(
                        conversation.provider, conversation.conversation_id, fingerprint,
                        conversation.title, status="failed", last_error=type(exc).__name__,
                    )
                raise

        if self.progress_store:
            # Reaching this point means every item in this file was audited now
            # or already had a completed matching fingerprint in the ledger.
            self.progress_store.record_source(
                source_provider, source_key, source_fingerprint or "", "complete",
                discovered_count=len(conversations), imported_count=len(conversations),
                checkpoint=conversations[-1].conversation_id if conversations else None,
            )
        return audits

    def consolidate(self, audits: Iterable[ConversationAudit]) -> dict:
        return self.consolidator.consolidate_candidates([x for a in audits for x in a.artifacts])

    def summarize(self, audits: Iterable[ConversationAudit]) -> dict:
        audits = list(audits)
        return {
            "conversation_count": len(audits),
            "artifact_count": sum(len(a.artifacts) for a in audits),
            "projects": sorted({a.suggested_project for a in audits if a.suggested_project}),
            "errors": sum(1 for a in audits for f in a.findings if f.severity == "error"),
            "warnings": sum(1 for a in audits for f in a.findings if f.severity == "warning"),
        }
