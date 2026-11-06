# DGM-MAT — Persistent Vault and project inventory

## Purpose

The Vault is local, portable data and must survive application upgrades or replacement. It is not the installed application directory and is not a Git repository. Never commit transcripts, message bodies, browser data or Vault databases.

## Configuration

By default, DGM-MAT uses a stable per-user data directory outside the installation and Git worktrees: `%LOCALAPPDATA%\\DGM-MAT\\Vault` on Windows, or `$XDG_DATA_HOME/DGM-MAT/Vault` (falling back to `~/.local/share/DGM-MAT/Vault`) on Linux/macOS. This means a normal application upgrade does not move or delete the Vault. Set `DGM_VAULT_PATH` only when you want to override that default with another persistent folder:

PowerShell (current session):

```powershell
$env:DGM_VAULT_PATH = 'C:\DGM-MAT-Vault'
```

For a permanent user-level setting, use the Windows Environment Variables interface after confirming the intended path and backup policy. Do not place the Vault under `C:\ProgramasGodMode\DGM-MAT\installed`.

## Layout

- `index/catalog.sqlite3` — searchable project, conversation, message, duplicate and tree index
- `providers/chrome-imports/` — immutable raw extension JSON imports
- `projects/<project-id>/conversations/` — immutable normalized transcript snapshots
- `projects/<project-id>/trees/` — timestamped JSON and readable TXT repository trees, plus `CURRENT.json`
- `quarantine/conversations/` — unclassified/ambiguous source material
- `missions/` — reserved for durable mission checkpoints

Exact duplicates and repeated messages/code are recorded as candidates with canonical provenance. No source material is deleted automatically.

## Synchronize existing completed conversation records and snapshot a repository

From the DGM-MAT repository root:

```powershell
python scripts\sync_dgm_vault.py --repository .
```

The command requires `DGM_VAULT_PATH`. It registers the DGM-MAT project, copies completed records from the local conversation progress database into the Vault, classifies only when there is evidence, sends uncertain items to quarantine, and creates a repository tree snapshot. It is safe to run again: identical captures are linked as duplicates.

To inventory a different repository, pass its path and register its project name/aliases explicitly:

```powershell
python scripts\sync_dgm_vault.py --repository 'C:\Projects\Example' --project-id example --project-name Example --aliases 'Example,Example Project'
```

## Live browser capture and archive import

When `DGM_VAULT_PATH` is configured, every live capture received by `/recovery/browser-capture/capture` writes both the exact raw JSON payload into `providers/browser-captures/<provider>/` and an immutable normalized transcript into the project Vault or quarantine. The API response reports `vault_status` and both Vault paths so a failed Vault copy is visible and can be retried. The Chrome archive importer separately copies downloaded inventory/export JSON into `providers/chrome-imports/` and imports normalized conversations. Without `DGM_VAULT_PATH`, the legacy runtime archive remains available but is not a substitute for the persistent Vault.

## Integrity and limits

- Original raw captures are copied, not moved or deleted.
- Archive files are SHA-256 verified and never overwritten.
- Conversation completeness is preserved as reported; unknown/partial does not become complete.
- Cross-provider transcript, message and code duplicates are indexed; candidates are not automatically discarded.
- Repository scanning is read-only, does not follow symlinks, ignores generated/vendor directories, and aborts without writing a partial snapshot when the entry limit is exceeded.
- The tree is an inventory, not yet a complete static analysis. Import/export resolution, dependency graph, bug detection and project gap analysis remain subsequent work.
- Back up the entire Vault (including SQLite WAL/checkpoint state) before migrations or moving it. Restore by setting `DGM_VAULT_PATH` to the restored directory; the catalogue is reopened from its local database.
