"""Safe, incremental importer for a ChatGPT conversations.json export.

The input export is read-only. Each conversation is archived separately, message
records retain the original message/node objects, and provider deletion is never
attempted. Attachment references are detected but attachments are not copied by
this first adapter, so such conversations remain explicitly partial.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from dataclasses import replace
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from core.recovery.recovery_ledger import RecoveryLedger, RecoverySource


class ChatGPTExportError(RuntimeError):
    """Raised when an export cannot be safely read or archived."""


@dataclass(frozen=True)
class ChatGPTImportReport:
    source_file: str
    discovered: int
    archived: int
    skipped_existing: int
    partial: int
    failed: int
    errors: tuple[str, ...]


def _iter_json_array(path: Path, chunk_size: int = 64 * 1024) -> Iterator[Any]:
    """Read a top-level JSON array one item at a time using only the stdlib."""
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8-sig") as stream:
        buffer = ""
        eof = False

        def fill() -> None:
            nonlocal buffer, eof
            if not eof:
                chunk = stream.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True

        while not buffer.strip() and not eof:
            fill()
        buffer = buffer.lstrip()
        if not buffer.startswith("["):
            raise ChatGPTExportError("Expected conversations.json to contain a top-level JSON array.")
        buffer = buffer[1:]

        while True:
            buffer = buffer.lstrip()
            while buffer.startswith(","):
                buffer = buffer[1:].lstrip()
            if buffer.startswith("]"):
                buffer = buffer[1:]
                if buffer.strip():
                    raise ChatGPTExportError("Unexpected content after the top-level JSON array.")
                while not eof:
                    fill()
                    if buffer.strip():
                        raise ChatGPTExportError("Unexpected content after the top-level JSON array.")
                return
            if not buffer and eof:
                raise ChatGPTExportError("Unexpected end of JSON array.")
            try:
                item, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if eof:
                    raise ChatGPTExportError("Malformed or truncated conversation JSON.")
                fill()
                continue
            yield item
            buffer = buffer[end:]
            if not buffer and not eof:
                fill()


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _source_date(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            pass
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown-date"


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return cleaned[:100] or hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _contains_attachment_reference(value: Any) -> bool:
    attachment_keys = {
        "attachments", "asset_pointer", "file_id", "file_ids",
        "image_asset_pointer", "audio_asset_pointer", "video_asset_pointer",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in attachment_keys and child not in (None, "", [], {}):
                return True
            if _contains_attachment_reference(child):
                return True
    elif isinstance(value, list):
        return any(_contains_attachment_reference(item) for item in value)
    return False


def _message_records(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = conversation.get("mapping")
    records: list[dict[str, Any]] = []
    if isinstance(mapping, dict):
        for node_id, node in mapping.items():
            if not isinstance(node, dict):
                continue
            message = node.get("message")
            timestamp = message.get("create_time") if isinstance(message, dict) else None
            records.append({
                "node_id": str(node_id),
                "parent": node.get("parent"),
                "children": node.get("children", []),
                "timestamp": timestamp,
                "role": (
                    message.get("author", {}).get("role", "unknown")
                    if isinstance(message, dict) and isinstance(message.get("author"), dict)
                    else "unknown"
                ),
                "message": message,
            })
    elif isinstance(conversation.get("messages"), list):
        for index, message in enumerate(conversation["messages"]):
            timestamp = message.get("create_time") if isinstance(message, dict) else None
            author = message.get("author", {}) if isinstance(message, dict) else {}
            records.append({
                "node_id": str(index),
                "parent": None,
                "children": [],
                "timestamp": timestamp,
                "role": author.get("role", "unknown") if isinstance(author, dict) else "unknown",
                "message": message,
            })
    # Preserve every branch/node; stable timestamp ordering is for indexing only.
    records.sort(key=lambda item: (
        item["timestamp"] if isinstance(item["timestamp"], (int, float)) else float("inf"),
        item["node_id"],
    ))
    return records


def import_chatgpt_conversations_json(
    source_file: str | Path,
    archive_root: str | Path,
    ledger: RecoveryLedger,
    *,
    original_location: str | None = None,
) -> ChatGPTImportReport:
    """Archive each export record and register it without changing/deleting the input."""
    source = Path(source_file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    root = Path(archive_root).expanduser().resolve() / "chatgpt"
    root.mkdir(parents=True, exist_ok=True)

    discovered = archived = skipped = partial = failed = 0
    errors: list[str] = []

    for index, item in enumerate(_iter_json_array(source)):
        discovered += 1
        if not isinstance(item, dict):
            failed += 1
            errors.append(f"record[{index}]: expected an object; record skipped")
            continue

        raw_id = item.get("id") or item.get("conversation_id")
        title = item.get("title")
        if not isinstance(raw_id, str) or not raw_id.strip():
            raw_id = hashlib.sha256(_stable_json(item).encode("utf-8")).hexdigest()[:32]
            errors.append(f"record[{index}]: missing conversation ID; deterministic fallback ID used")
        source_id = raw_id.strip()
        if not isinstance(title, str) or not title.strip():
            title = f"Untitled conversation {source_id[:12]}"

        destination = root / f"{_safe_id(source_id)}.conversation.json"
        serialized = _stable_json(item)
        encoded = serialized.encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()

        existing = ledger.get("chatgpt", source_id)
        if existing is not None:
            if existing.raw_sha256 == digest and existing.raw_archive_path:
                existing_path = Path(existing.raw_archive_path)
                if existing_path.is_file() and RecoveryLedger.sha256_file(existing_path) == digest:
                    skipped += 1
                    continue
            failed += 1
            errors.append(f"record[{index}] ({source_id}): source already registered with different or unverifiable archive; not overwritten")
            continue

        if destination.exists():
            if RecoveryLedger.sha256_file(destination) != digest:
                failed += 1
                errors.append(f"record[{index}] ({source_id}): archive path collision; existing file preserved")
                continue
        else:
            # Exclusive creation prevents silently replacing a previous recovery artifact.
            try:
                with destination.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(serialized)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError:
                if RecoveryLedger.sha256_file(destination) != digest:
                    failed += 1
                    errors.append(f"record[{index}] ({source_id}): concurrent archive collision; existing file preserved")
                    continue

        records = _message_records(item)
        messages_path = root / f"{_safe_id(source_id)}.messages.jsonl"
        lines = "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        )
        if messages_path.exists():
            # Derived indexes are rebuildable, but never overwrite an unverified prior output.
            if messages_path.read_text(encoding="utf-8") != lines:
                failed += 1
                errors.append(f"record[{index}] ({source_id}): derived message file conflicts; source archive preserved")
                continue
        else:
            try:
                with messages_path.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(lines)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError:
                if messages_path.read_text(encoding="utf-8") != lines:
                    failed += 1
                    errors.append(f"record[{index}] ({source_id}): concurrent message-file collision")
                    continue

        has_attachments = _contains_attachment_reference(item)
        is_partial = has_attachments or not records
        state = "partial" if is_partial else "captured"
        completeness = "partial" if is_partial else "unknown"
        ledger.register(RecoverySource(
            provider="chatgpt",
            source_id=source_id,
            title=title,
            source_date=_source_date(item.get("create_time") or item.get("created_at")),
            source_url="",
            original_location=original_location or str(source),
            capture_status=state,
            raw_archive_path=str(destination),
            raw_sha256=digest,
            completeness=completeness,
            index_status="pending",
            repo_status="pending",
            deletion_status="not_eligible",
            last_error="attachment references detected; attachment files not copied" if has_attachments else "",
        ))
        archived += 1
        if is_partial:
            partial += 1

    return ChatGPTImportReport(
        source_file=str(source),
        discovered=discovered,
        archived=archived,
        skipped_existing=skipped,
        partial=partial,
        failed=failed,
        errors=tuple(errors),
    )

def import_chatgpt_export_zip(
    zip_file: str | Path,
    archive_root: str | Path,
    ledger: RecoveryLedger,
    *,
    max_conversations_json_bytes: int = 512 * 1024 * 1024,
) -> ChatGPTImportReport:
    """Safely import conversations.json from a ZIP without extracting arbitrary paths.

    The ZIP is opened read-only. Only the uniquely identified conversations.json member
    is streamed into a private temporary directory; no member-supplied path is written to
    disk. Attachment files remain unextracted and referenced conversations remain partial.
    """
    source_zip = Path(zip_file).expanduser().resolve()
    if not source_zip.is_file():
        raise FileNotFoundError(source_zip)
    if max_conversations_json_bytes < 1:
        raise ValueError("max_conversations_json_bytes must be positive.")

    try:
        with zipfile.ZipFile(source_zip, "r") as archive:
            candidates = [
                info for info in archive.infolist()
                if not info.is_dir() and Path(info.filename.replace("\\\\", "/")).name.casefold() == "conversations.json"
            ]
            if len(candidates) != 1:
                raise ChatGPTExportError(
                    f"Expected exactly one conversations.json member; found {len(candidates)}."
                )
            member = candidates[0]
            if member.file_size > max_conversations_json_bytes:
                raise ChatGPTExportError(
                    f"conversations.json exceeds configured size limit ({max_conversations_json_bytes} bytes)."
                )

            root = Path(archive_root).expanduser().resolve()
            root.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(prefix="dgm-chatgpt-import-", dir=str(root)) as staging:
                staged_json = Path(staging) / "conversations.json"
                copied = 0
                with archive.open(member, "r") as src, staged_json.open("xb") as dst:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        copied += len(chunk)
                        if copied > max_conversations_json_bytes:
                            raise ChatGPTExportError("conversations.json exceeded size limit while streaming.")
                        dst.write(chunk)
                    dst.flush()
                    os.fsync(dst.fileno())
                if copied != member.file_size:
                    raise ChatGPTExportError("ZIP member size differs from bytes read; archive may be truncated.")
                report = import_chatgpt_conversations_json(
                    staged_json, root, ledger, original_location=str(source_zip)
                )
                return replace(report, source_file=str(source_zip))
    except zipfile.BadZipFile as exc:
        raise ChatGPTExportError("Input is not a valid ZIP archive.") from exc
\n