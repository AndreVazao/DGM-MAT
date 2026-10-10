from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import AIProposal, ConversationRelation, UserDecision, UserIntent


class ConversationKnowledgeStore:
    """Durable evidence-linked knowledge; reviewed user truth is never silently overwritten."""

    SCHEMA_VERSION = 1

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS user_intents (
                    intent_id TEXT PRIMARY KEY,
                    statement TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('current','confirmed','superseded','legacy','conflict','unverified','retracted')),
                    source_conversation_id TEXT,
                    source_message_id TEXT,
                    observed_at TEXT,
                    supersedes_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                    reviewed_by_user INTEGER NOT NULL CHECK(reviewed_by_user IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS ai_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    statement TEXT NOT NULL,
                    source_conversation_id TEXT NOT NULL,
                    source_message_id TEXT,
                    accepted INTEGER CHECK(accepted IN (0,1) OR accepted IS NULL),
                    decision_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS user_decisions (
                    decision_id TEXT PRIMARY KEY,
                    statement TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('confirmed','superseded','retracted','unverified')),
                    source_conversation_id TEXT,
                    source_message_id TEXT,
                    decided_at TEXT,
                    supersedes_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    confirmed_by_user INTEGER NOT NULL CHECK(confirmed_by_user IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS conversation_relations (
                    relation_id TEXT PRIMARY KEY,
                    source_conversation_id TEXT NOT NULL,
                    target_conversation_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL CHECK(relation_type IN ('same_project','continues','supersedes','conflicts_with','duplicates','references')),
                    evidence_json TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                    reviewed_by_user INTEGER NOT NULL CHECK(reviewed_by_user IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(source_conversation_id, target_conversation_id, relation_type)
                );
                CREATE TABLE IF NOT EXISTS review_tasks (
                    task_id TEXT PRIMARY KEY,
                    item_type TEXT NOT NULL CHECK(item_type IN ('intent','proposal','decision','relation','coverage','artifact')),
                    item_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('open','resolved','cancelled')),
                    evidence_json TEXT NOT NULL,
                    resolution TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    UNIQUE(item_type, item_id, reason, status)
                );
                CREATE TABLE IF NOT EXISTS knowledge_history (
                    event_no INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL CHECK(entity_type IN ('intent','proposal','decision','relation','review_task')),
                    entity_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_knowledge_history_entity
                    ON knowledge_history(entity_type, entity_id, event_no);
                CREATE INDEX IF NOT EXISTS ix_intents_status ON user_intents(status, reviewed_by_user);
                CREATE INDEX IF NOT EXISTS ix_decisions_status ON user_decisions(status, confirmed_by_user);
                CREATE INDEX IF NOT EXISTS ix_relations_source ON conversation_relations(source_conversation_id);
                CREATE INDEX IF NOT EXISTS ix_review_tasks_status ON review_tasks(status, item_type);
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.database_path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        value = dict(row)
        for key in ("supersedes_json", "evidence_json"):
            if key in value:
                value[key.removesuffix("_json")] = json.loads(value.pop(key))
        for key in ("reviewed_by_user", "confirmed_by_user"):
            if key in value:
                value[key] = bool(value[key])
        if "accepted" in value and value["accepted"] is not None:
            value["accepted"] = bool(value["accepted"])
        return value

    def _record_history(self, db: sqlite3.Connection, entity_type: str, entity_id: str, event_type: str, payload: dict) -> None:
        db.execute(
            "INSERT INTO knowledge_history (entity_type, entity_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (entity_type, entity_id, event_type, self._json(payload), self._now()),
        )

    def history(self, entity_type: str, entity_id: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT event_no, entity_type, entity_id, event_type, payload_json, created_at FROM knowledge_history WHERE entity_type=? AND entity_id=? ORDER BY event_no",
                (entity_type, entity_id),
            ).fetchall()
        return [
            {**dict(row), "payload": json.loads(row["payload_json"])}
            for row in rows
        ]

    def save_intent(self, intent: UserIntent) -> None:
        if not intent.intent_id.strip() or not intent.statement.strip():
            raise ValueError("intent_id and statement are required")
        if not 0 <= intent.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        now = self._now()
        with self._connect() as db:
            existing = db.execute("SELECT * FROM user_intents WHERE intent_id=?", (intent.intent_id,)).fetchone()
            if existing and (
                existing["statement"] == intent.statement
                and existing["status"] == intent.status
                and existing["source_conversation_id"] == intent.source_conversation_id
                and existing["source_message_id"] == intent.source_message_id
                and existing["observed_at"] == intent.observed_at
                and existing["supersedes_json"] == self._json(intent.supersedes)
                and existing["evidence_json"] == self._json(intent.evidence)
                and existing["confidence"] == intent.confidence
                and bool(existing["reviewed_by_user"]) == intent.reviewed_by_user
            ):
                return
            if existing and existing["reviewed_by_user"]:
                if (existing["statement"] != intent.statement
                        or existing["status"] != intent.status
                        or not intent.reviewed_by_user):
                    raise ValueError("Reviewed intent is immutable without an explicit reviewed migration")
                return
            db.execute("""
                INSERT INTO user_intents (
                    intent_id, statement, status, source_conversation_id, source_message_id,
                    observed_at, supersedes_json, evidence_json, confidence, reviewed_by_user,
                    created_at, updated_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(intent_id) DO UPDATE SET
                    statement=excluded.statement, status=excluded.status,
                    source_conversation_id=excluded.source_conversation_id,
                    source_message_id=excluded.source_message_id, observed_at=excluded.observed_at,
                    supersedes_json=excluded.supersedes_json, evidence_json=excluded.evidence_json,
                    confidence=excluded.confidence, reviewed_by_user=excluded.reviewed_by_user,
                    updated_at=excluded.updated_at, schema_version=excluded.schema_version
            """, (
                intent.intent_id, intent.statement, intent.status, intent.source_conversation_id,
                intent.source_message_id, intent.observed_at, self._json(intent.supersedes),
                self._json(intent.evidence), intent.confidence, int(intent.reviewed_by_user),
                now, now, self.SCHEMA_VERSION,
            ))
            self._record_history(db, "intent", intent.intent_id, "saved", {
                "statement": intent.statement, "status": intent.status,
                "source_conversation_id": intent.source_conversation_id,
                "source_message_id": intent.source_message_id, "observed_at": intent.observed_at,
                "supersedes": intent.supersedes, "evidence": intent.evidence,
                "confidence": intent.confidence, "reviewed_by_user": intent.reviewed_by_user,
            })

    def get_intent(self, intent_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM user_intents WHERE intent_id=?", (intent_id,)).fetchone()
        return self._row(row)

    def list_intents(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM user_intents"
        params: tuple = ()
        if status is not None:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY observed_at, intent_id"
        with self._connect() as db:
            return [self._row(row) for row in db.execute(query, params).fetchall()]

    def save_proposal(self, proposal: AIProposal) -> None:
        if not proposal.proposal_id.strip() or not proposal.statement.strip() or not proposal.source_conversation_id.strip():
            raise ValueError("proposal id, statement and source conversation are required")
        now = self._now()
        accepted = None if proposal.accepted is None else int(proposal.accepted)
        with self._connect() as db:
            existing = db.execute("SELECT * FROM ai_proposals WHERE proposal_id=?", (proposal.proposal_id,)).fetchone()
            if existing and (
                existing["statement"] == proposal.statement
                and existing["source_conversation_id"] == proposal.source_conversation_id
                and existing["source_message_id"] == proposal.source_message_id
                and existing["accepted"] == accepted
                and existing["decision_id"] == proposal.decision_id
            ):
                return
            if existing and existing["accepted"] is not None:
                # Once a user has accepted/rejected a proposal, preserve the full
                # provenance chain as well as its text and decision state.
                if (existing["accepted"] != accepted
                        or existing["statement"] != proposal.statement
                        or existing["source_conversation_id"] != proposal.source_conversation_id
                        or existing["source_message_id"] != proposal.source_message_id
                        or existing["decision_id"] != proposal.decision_id):
                    raise ValueError("An explicitly accepted/rejected proposal cannot be silently rewritten")
            db.execute("""
                INSERT INTO ai_proposals (
                    proposal_id, statement, source_conversation_id, source_message_id,
                    accepted, decision_id, created_at, updated_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(proposal_id) DO UPDATE SET
                    statement=excluded.statement, source_conversation_id=excluded.source_conversation_id,
                    source_message_id=excluded.source_message_id, accepted=excluded.accepted,
                    decision_id=excluded.decision_id, updated_at=excluded.updated_at,
                    schema_version=excluded.schema_version
            """, (
                proposal.proposal_id, proposal.statement, proposal.source_conversation_id,
                proposal.source_message_id, accepted, proposal.decision_id, now, now, self.SCHEMA_VERSION,
            ))
            self._record_history(db, "proposal", proposal.proposal_id, "saved", {
                "statement": proposal.statement, "source_conversation_id": proposal.source_conversation_id,
                "source_message_id": proposal.source_message_id, "accepted": proposal.accepted,
                "decision_id": proposal.decision_id,
            })

    def list_proposals(self, accepted: bool | None = None) -> list[dict]:
        query = "SELECT * FROM ai_proposals"
        params: tuple = ()
        if accepted is not None:
            query += " WHERE accepted=?"
            params = (int(accepted),)
        query += " ORDER BY created_at, proposal_id"
        with self._connect() as db:
            return [self._row(row) for row in db.execute(query, params).fetchall()]

    def save_decision(self, decision: UserDecision) -> None:
        if not decision.decision_id.strip() or not decision.statement.strip():
            raise ValueError("decision_id and statement are required")
        now = self._now()
        with self._connect() as db:
            existing = db.execute("SELECT * FROM user_decisions WHERE decision_id=?", (decision.decision_id,)).fetchone()
            if existing and (
                existing["statement"] == decision.statement
                and existing["status"] == decision.status
                and existing["source_conversation_id"] == decision.source_conversation_id
                and existing["source_message_id"] == decision.source_message_id
                and existing["decided_at"] == decision.decided_at
                and existing["supersedes_json"] == self._json(decision.supersedes)
                and existing["evidence_json"] == self._json(decision.evidence)
                and bool(existing["confirmed_by_user"]) == decision.confirmed_by_user
            ):
                return
            if existing and existing["confirmed_by_user"]:
                if (existing["statement"] != decision.statement
                        or existing["status"] != decision.status
                        or not decision.confirmed_by_user):
                    raise ValueError("User-confirmed decision is immutable without an explicit reviewed migration")
                return
            db.execute("""
                INSERT INTO user_decisions (
                    decision_id, statement, status, source_conversation_id, source_message_id,
                    decided_at, supersedes_json, evidence_json, confirmed_by_user,
                    created_at, updated_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id) DO UPDATE SET
                    statement=excluded.statement, status=excluded.status,
                    source_conversation_id=excluded.source_conversation_id,
                    source_message_id=excluded.source_message_id, decided_at=excluded.decided_at,
                    supersedes_json=excluded.supersedes_json, evidence_json=excluded.evidence_json,
                    confirmed_by_user=excluded.confirmed_by_user, updated_at=excluded.updated_at,
                    schema_version=excluded.schema_version
            """, (
                decision.decision_id, decision.statement, decision.status, decision.source_conversation_id,
                decision.source_message_id, decision.decided_at, self._json(decision.supersedes),
                self._json(decision.evidence), int(decision.confirmed_by_user), now, now, self.SCHEMA_VERSION,
            ))
            self._record_history(db, "decision", decision.decision_id, "saved", {
                "statement": decision.statement, "status": decision.status,
                "source_conversation_id": decision.source_conversation_id,
                "source_message_id": decision.source_message_id, "decided_at": decision.decided_at,
                "supersedes": decision.supersedes, "evidence": decision.evidence,
                "confirmed_by_user": decision.confirmed_by_user,
            })

    def get_decision(self, decision_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM user_decisions WHERE decision_id=?", (decision_id,)).fetchone()
        return self._row(row)

    def list_decisions(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM user_decisions"
        params: tuple = ()
        if status is not None:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY decided_at, decision_id"
        with self._connect() as db:
            return [self._row(row) for row in db.execute(query, params).fetchall()]

    def save_relation(self, relation: ConversationRelation) -> None:
        if relation.source_conversation_id == relation.target_conversation_id:
            raise ValueError("A conversation cannot be related to itself")
        if not 0 <= relation.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        now = self._now()
        with self._connect() as db:
            existing = db.execute("SELECT * FROM conversation_relations WHERE relation_id=?", (relation.relation_id,)).fetchone()
            if existing and (
                existing["source_conversation_id"] == relation.source_conversation_id
                and existing["target_conversation_id"] == relation.target_conversation_id
                and existing["relation_type"] == relation.relation_type
                and existing["evidence_json"] == self._json(relation.evidence)
                and existing["confidence"] == relation.confidence
                and bool(existing["reviewed_by_user"]) == relation.reviewed_by_user
            ):
                return
            if existing and existing["reviewed_by_user"]:
                if (existing["source_conversation_id"] != relation.source_conversation_id
                        or existing["target_conversation_id"] != relation.target_conversation_id
                        or existing["relation_type"] != relation.relation_type
                        or not relation.reviewed_by_user):
                    raise ValueError("Reviewed relation is immutable without an explicit reviewed migration")
                return
            db.execute("""
                INSERT INTO conversation_relations (
                    relation_id, source_conversation_id, target_conversation_id, relation_type,
                    evidence_json, confidence, reviewed_by_user, created_at, updated_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(relation_id) DO UPDATE SET
                    source_conversation_id=excluded.source_conversation_id,
                    target_conversation_id=excluded.target_conversation_id,
                    relation_type=excluded.relation_type, evidence_json=excluded.evidence_json,
                    confidence=excluded.confidence, reviewed_by_user=excluded.reviewed_by_user,
                    updated_at=excluded.updated_at, schema_version=excluded.schema_version
            """, (
                relation.relation_id, relation.source_conversation_id, relation.target_conversation_id,
                relation.relation_type, self._json(relation.evidence), relation.confidence,
                int(relation.reviewed_by_user), now, now, self.SCHEMA_VERSION,
            ))
            self._record_history(db, "relation", relation.relation_id, "saved", {
                "source_conversation_id": relation.source_conversation_id,
                "target_conversation_id": relation.target_conversation_id,
                "relation_type": relation.relation_type, "evidence": relation.evidence,
                "confidence": relation.confidence, "reviewed_by_user": relation.reviewed_by_user,
            })

    def list_relations(self, conversation_id: str | None = None) -> list[dict]:
        query = "SELECT * FROM conversation_relations"
        params: tuple = ()
        if conversation_id is not None:
            query += " WHERE source_conversation_id=? OR target_conversation_id=?"
            params = (conversation_id, conversation_id)
        query += " ORDER BY source_conversation_id, target_conversation_id, relation_type"
        with self._connect() as db:
            rows = [dict(row) for row in db.execute(query, params).fetchall()]
        for row in rows:
            row["evidence"] = json.loads(row.pop("evidence_json"))
            row["reviewed_by_user"] = bool(row["reviewed_by_user"])
        return rows

    def create_review_task(
        self, *, task_id: str, item_type: str, item_id: str, reason: str,
        evidence: list[str] | None = None,
    ) -> dict:
        if not task_id.strip() or not item_id.strip() or not reason.strip():
            raise ValueError("task_id, item_id and reason are required")
        now = self._now()
        with self._connect() as db:
            inserted = db.execute("""
                INSERT INTO review_tasks (task_id, item_type, item_id, reason, status, evidence_json, created_at)
                VALUES (?, ?, ?, ?, 'open', ?, ?)
                ON CONFLICT(task_id) DO NOTHING
            """, (task_id, item_type, item_id, reason, self._json(evidence or []), now))
            row = db.execute("SELECT * FROM review_tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is not None and inserted.rowcount == 1:
                payload = dict(row)
                payload["evidence"] = json.loads(payload.pop("evidence_json"))
                self._record_history(db, "review_task", task_id, "created", payload)
        return self._row(row) or {}

    def resolve_review_task(self, task_id: str, *, resolution: str, evidence: list[str]) -> bool:
        if not resolution.strip() or not evidence:
            raise ValueError("resolution and evidence are required")
        with self._connect() as db:
            updated = db.execute("""
                UPDATE review_tasks SET status='resolved', resolution=?, evidence_json=?, resolved_at=?
                WHERE task_id=? AND status='open'
            """, (resolution, self._json(evidence), self._now(), task_id))
            if updated.rowcount == 1:
                row = db.execute("SELECT * FROM review_tasks WHERE task_id=?", (task_id,)).fetchone()
                self._record_history(db, "review_task", task_id, "resolved", dict(row))
            return updated.rowcount == 1

    def list_open_review_tasks(self) -> list[dict]:
        with self._connect() as db:
            rows = [dict(row) for row in db.execute(
                "SELECT * FROM review_tasks WHERE status='open' ORDER BY created_at, task_id"
            ).fetchall()]
        for row in rows:
            row["evidence"] = json.loads(row.pop("evidence_json"))
        return rows

    def summary(self) -> dict[str, int]:
        with self._connect() as db:
            result = {}
            for table, prefix in (
                ("user_intents", "intents"),
                ("ai_proposals", "proposals"),
                ("user_decisions", "decisions"),
                ("conversation_relations", "relations"),
                ("review_tasks", "review_tasks"),
            ):
                rows = db.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
                result[prefix] = int(rows["n"])
            open_tasks = db.execute("SELECT COUNT(*) AS n FROM review_tasks WHERE status='open'").fetchone()
            result["review_tasks_open"] = int(open_tasks["n"])
            return result
