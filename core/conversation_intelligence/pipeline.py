from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .auditor import CodeConsolidator, ConversationAuditor
from .code_extractor import CodeExtractor
from .ingest import ConversationIngestor
from .models import (
    ArtifactProvenance,
    AuditFinding,
    CodeArtifact,
    ConversationAudit,
    ConversationRecord,
)
from .progress_store import ConversationProgressStore
from .knowledge_store import ConversationKnowledgeStore


class ConversationIntelligencePipeline:
    def __init__(self, progress_store_path: str | Path | None = None, knowledge_store_path: str | Path | None = None) -> None:
        self.ingestor = ConversationIngestor()
        self.extractor = CodeExtractor()
        self.auditor = ConversationAuditor()
        self.consolidator = CodeConsolidator()
        self.progress_store = ConversationProgressStore(progress_store_path) if progress_store_path else None
        self.knowledge_store = ConversationKnowledgeStore(knowledge_store_path) if knowledge_store_path else None

    @staticmethod
    def _audit_to_snapshot(audit: ConversationAudit) -> dict:
        """Persist reusable derived knowledge, not the full raw conversation transcript."""
        return {
            "conversation": {
                "conversation_id": audit.conversation.conversation_id,
                "provider": audit.conversation.provider,
                "title": audit.conversation.title,
                "source": audit.conversation.source,
                "url": audit.conversation.url,
                "detected_projects": audit.conversation.detected_projects,
                "tags": audit.conversation.tags,
                "metadata": audit.conversation.metadata,
            },
            "artifacts": [asdict(artifact) for artifact in audit.artifacts],
            "findings": [asdict(finding) for finding in audit.findings],
            "suggested_project": audit.suggested_project,
            "suggested_title": audit.suggested_title,
        }

    @staticmethod
    def _snapshot_to_audit(snapshot: dict, current: ConversationRecord | None = None) -> ConversationAudit:
        stored_conversation = snapshot.get("conversation", {})
        conversation = current or ConversationRecord(
            conversation_id=stored_conversation.get("conversation_id", ""),
            provider=stored_conversation.get("provider", "unknown"),
            title=stored_conversation.get("title", "Imported conversation"),
            content="",
            source=stored_conversation.get("source", "progress-store"),
            url=stored_conversation.get("url"),
            detected_projects=stored_conversation.get("detected_projects", []),
            tags=stored_conversation.get("tags", []),
            metadata=stored_conversation.get("metadata", {}),
        )
        artifacts = []
        for item in snapshot.get("artifacts", []):
            item = dict(item)
            provenance = item.get("provenance")
            if provenance:
                item["provenance"] = ArtifactProvenance(**provenance)
            artifacts.append(CodeArtifact(**item))
        findings = [AuditFinding(**item) for item in snapshot.get("findings", [])]
        return ConversationAudit(
            conversation=conversation,
            artifacts=artifacts,
            findings=findings,
            suggested_project=snapshot.get("suggested_project"),
            suggested_title=snapshot.get("suggested_title"),
        )

    def load_saved_audits(self, provider: str | None = None) -> list[ConversationAudit]:
        """Load reusable audited knowledge from the ledger without rereading source exports."""
        if not self.progress_store:
            return []
        result = []
        for row in self.progress_store.list_conversations(provider):
            if row.get("status") != "complete" or not row.get("result"):
                continue
            result.append(self._snapshot_to_audit(row["result"]))
        return result

    def ingest_file(self, path: str | Path, provider: str | None = None) -> list[ConversationAudit]:
        source_path = Path(path)
        source_provider = self.ingestor.normalize_provider(provider or source_path.stem)
        source_key = str(source_path.resolve())
        source_fingerprint = self.progress_store.fingerprint(source_path.read_bytes()) if self.progress_store else None

        # Fast path: a byte-identical, previously completed source can return its
        # saved audit snapshots without reparsing the export or revisiting turns.
        if self.progress_store and source_fingerprint is not None:
            source_state = self.progress_store.get_source(source_provider, source_key)
            if (source_state and source_state.get("status") == "complete"
                    and source_state.get("source_fingerprint") == source_fingerprint):
                cached_ids = self.progress_store.list_source_conversations(
                    source_provider, source_key, source_fingerprint
                )
                if len(cached_ids) == source_state.get("discovered_count"):
                    cached_audits: list[ConversationAudit] = []
                    for conversation_id in cached_ids:
                        saved = self.progress_store.get_conversation(source_provider, conversation_id)
                        snapshot = saved.get("result") if saved and saved.get("status") == "complete" else None
                        if not (isinstance(snapshot, dict)
                                and isinstance(snapshot.get("conversation"), dict)
                                and isinstance(snapshot.get("artifacts"), list)):
                            break
                        cached_audits.append(self._snapshot_to_audit(snapshot))
                    else:
                        return cached_audits

        conversations = self.ingestor.load_file(source_path, provider)
        audits: list[ConversationAudit] = []
        if self.progress_store:
            self.progress_store.record_source(
                source_provider, source_key, source_fingerprint or "", "partial",
                discovered_count=len(conversations), imported_count=0, checkpoint=None,
            )

        processed_count = 0
        try:
            for conversation in conversations:
                fingerprint = None
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
                        saved = self.progress_store.get_conversation(conversation.provider, conversation.conversation_id)
                        snapshot = saved.get("result") if saved else None
                        # Older ledger versions stored counters only. Rebuild those
                        # records once rather than returning a misleading empty audit.
                        if isinstance(snapshot, dict) and isinstance(snapshot.get("conversation"), dict) and isinstance(snapshot.get("artifacts"), list):
                            audits.append(self._snapshot_to_audit(snapshot, current=conversation))
                            processed_count += 1
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
                            conversation.provider, conversation.conversation_id, fingerprint or "",
                            conversation.title, status="complete",
                            result=self._audit_to_snapshot(audit),
                        )
                    processed_count += 1
                except Exception as exc:
                    if self.progress_store:
                        self.progress_store.record_conversation(
                            conversation.provider, conversation.conversation_id, fingerprint or "",
                            conversation.title, status="failed", last_error=type(exc).__name__,
                        )
                    raise

            if self.progress_store:
                self.progress_store.set_source_conversations(
                    source_provider, source_key, source_fingerprint or "",
                    [conversation.conversation_id for conversation in conversations],
                )
                self.progress_store.record_source(
                    source_provider, source_key, source_fingerprint or "", "complete",
                    discovered_count=len(conversations), imported_count=processed_count,
                    checkpoint=conversations[-1].conversation_id if conversations else None,
                )
        except Exception as exc:
            if self.progress_store:
                self.progress_store.record_source(
                    source_provider, source_key, source_fingerprint or "", "failed",
                    discovered_count=len(conversations), imported_count=processed_count,
                    checkpoint=conversations[processed_count - 1].conversation_id if processed_count else None,
                    last_error=type(exc).__name__,
                )
            raise
        return audits

    def build_delegation_context(self, provider: str | None = None) -> dict:
        """Provide delegations with cached archive knowledge and open reviews, without rereading exports."""
        audits = self.load_saved_audits(provider)
        conversations = []
        for audit in audits:
            conversations.append({
                "conversation_id": audit.conversation.conversation_id,
                "provider": audit.conversation.provider,
                "title": audit.conversation.title,
                "url": audit.conversation.url,
                "suggested_project": audit.suggested_project,
                "suggested_title": audit.suggested_title,
                "findings": [asdict(finding) for finding in audit.findings],
                "artifacts": [{
                    "artifact_id": artifact.artifact_id,
                    "language": artifact.language,
                    "file_path": artifact.file_path,
                    "fingerprint": artifact.fingerprint,
                    "code": artifact.code,
                    "provenance": asdict(artifact.provenance) if artifact.provenance else None,
                } for artifact in audit.artifacts],
            })
        context = {
            "archive_summary": self.summarize(audits),
            "conversations": conversations,
            "open_review_tasks": [],
            "knowledge": {},
        }
        if self.knowledge_store:
            context["open_review_tasks"] = self.knowledge_store.list_open_review_tasks()
            context["knowledge"] = {
                "summary": self.knowledge_store.summary(),
                "intents": self.knowledge_store.list_intents(),
                "proposals": self.knowledge_store.list_proposals(),
                "decisions": self.knowledge_store.list_decisions(),
                "relations": self.knowledge_store.list_relations(),
            }
        return context

    def consolidate(self, audits: Iterable[ConversationAudit] | None = None) -> dict:
        selected = list(audits) if audits is not None else self.load_saved_audits()
        return self.consolidator.consolidate_candidates([artifact for audit in selected for artifact in audit.artifacts])

    def summarize(self, audits: Iterable[ConversationAudit] | None = None) -> dict:
        selected = list(audits) if audits is not None else self.load_saved_audits()
        return {
            "conversation_count": len(selected),
            "artifact_count": sum(len(audit.artifacts) for audit in selected),
            "projects": sorted({audit.suggested_project for audit in selected if audit.suggested_project}),
            "errors": sum(1 for audit in selected for finding in audit.findings if finding.severity == "error"),
            "warnings": sum(1 for audit in selected for finding in audit.findings if finding.severity == "warning"),
        }
