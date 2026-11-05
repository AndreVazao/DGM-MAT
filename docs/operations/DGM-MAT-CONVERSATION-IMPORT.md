# DGM-MAT — conversation import and role-preserving memory

## Design

Conversation imports are append-only and source-aware. Each imported turn preserves the speaker:
- `UTILIZADOR` / `user`: the original request or instruction;
- the provider name / `assistant`: the AI response;
- missing responses are marked as missing, never reconstructed.

User requirements are not overwritten by later AI suggestions. A future requirement ledger must keep the original request, later amendments, the current effective requirement, source conversation and decision date as separate records.

## Telescope / Claude Code

The metadata-only `TelescopeAdapter` remains metadata-only. Full transcript import is a separate, explicit operator action through `TelescopeArchiveImporter`.

- `GET /runtime/conversations/telescope/status` — import coverage and counts only.
- `POST /runtime/conversations/telescope/import` — exports sessions and turns with Telescope CLI and imports the redacted transcripts.
- `tele sessions get` is not used. The importer uses `tele export json`.
- Each session becomes one UTF-8 Markdown file under the configured archive root, in the `claude-code` folder.
- User and assistant messages are stored as separate Markdown sections and separate normalized message records.
- API keys, bearer tokens, common provider tokens and private-key blocks are redacted.
- Absolute working-directory metadata, last-message fields and opaque metadata are not imported. Literal paths that already occur inside the user's or AI's message text are retained as conversation content, except for the secret-redaction rules.
- Re-imports are idempotent; unchanged session files are not rewritten.
- A redacted normalized JSON cache is passed to Conversation Intelligence for local indexing.

Recommended setting:
`DGM_CONVERSATION_ARCHIVE_DIR=C:\\ProgramasGodMode\\DGM-MAT-Data\\conversations`

## ChatGPT, Gemini and Grok

The local Chrome source inventory reads only application indicators and browser-history metadata. It does not read page bodies, IndexedDB content, cookies or tokens.

- ChatGPT export ZIP or JSON is supported by the recovery importer.
- `GET /recovery/inbox` lists files in the local intake folder without reading their contents.
- `POST /recovery/import/inbox` imports supported ChatGPT ZIP/JSON exports.
- Gemini and Grok exports are inventoried but remain untouched until their actual export schemas are validated. The system does not guess their formats.

Recommended setting:
`DGM_CONVERSATION_IMPORT_DIR=C:\\ProgramasGodMode\\DGM-MAT-Data\\conversation-imports`

## Project association

A conversation is associated with a repository only when its recorded working directory maps to an inventoried repository. Otherwise, only a safe directory leaf is retained as a weak hint. No absolute user profile path is written into the Markdown archive.

## Integrity and retention

- Original provider exports are never modified or deleted.
- Every ChatGPT archive has a SHA-256 integrity record in the recovery ledger.
- Telescope Markdown archives are content-hashed in the manifest.
- Re-importing unchanged data does not create duplicate session records.
- Provider deletion is never attempted.
