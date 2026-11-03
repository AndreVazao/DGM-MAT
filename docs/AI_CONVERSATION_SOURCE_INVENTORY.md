# DGM-MAT — Local AI Conversation Source Inventory

**Scope:** local Chrome app indicators and browser-history metadata only.

## What it does

- Detects ChatGPT, Grok and Gemini Chrome application shortcuts.
- Inspects Chrome profile directory names for provider-specific IndexedDB origins; it never reads IndexedDB values.
- Reads the Chrome History main SQLite database in immutable/read-only mode.
- Extracts only provider URL host, conversation route ID, page title, visit timestamp and visit count.
- Deduplicates project-prefixed and direct URLs by provider conversation ID.
- Marks the result incomplete because browser history is not a provider export and immutable mode excludes uncheckpointed WAL entries.
- Can prepare a local export intake directory without overwriting existing files.

## What it never does

- Reads cookies, tokens, passwords, local-storage values or IndexedDB contents.
- Opens provider accounts, sends messages or changes/deletes provider data.
- Claims that browser metadata is a complete transcript inventory.
- Writes private conversation titles into the Git repository. Reports are generated locally.

## Windows usage

From a DGM-MAT checkout:

```powershell
python scripts/inventory_ai_conversation_sources.py --limit 100
python scripts/inventory_ai_conversation_sources.py --limit 100 --prepare-inbox --output "$env:LOCALAPPDATA\DGM-MAT\diagnostics\AI-CONVERSATION-SOURCE-INVENTORY.json"
```

Default export intake root:

`%LOCALAPPDATA%\DGM-MAT\recovery-inbox\`

Provider folders: `chatgpt`, `gemini`, `grok`, `_unknown`.

The JSON report includes URL-row counts and deduplicated conversation route counts. It may include conversation titles and paths, so keep it in the private local diagnostics directory; do not commit it to a public repository.

## Operator API

`GET /recovery/local-ai-sources?limit=100`

The route is operator-only, bounded to 1–500 metadata entries per provider, and does not read transcript bodies or credentials. It can be used by the cockpit to display source presence and inventory progress.

## Current implementation boundary

The inventory is metadata-only. Provider export archives are still required for complete conversation ingestion and semantic indexing. The report intentionally sets `complete_conversation_inventory=false`.