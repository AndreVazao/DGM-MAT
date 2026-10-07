# DGM-MAT Connectors Boundary Checkpoint — 2026-10-07

## Scope

The next extraction gate after Agents was audited around `core/connectors`.

## Consumer audit

- `core/api/runtime_api.py` is the only active production consumer of the Obsidian connector.
- No other active production/test module imports `core.connectors` directly.
- The two adapter files under `core/connectors/adapters` are placeholders with no active consumers and were not promoted.

## Extraction

A standalone `DGM-MAT-Connectors` package was established:

- package: `dgm_mat_connectors`
- implementation: `ObsidianConnector`
- tests: 2 passing
- no `core.*` imports in the standalone connector
- configurable vault path through `DGM_OBSIDIAN_VAULT`
- fallback through `DGM_BASE_PATH/storage/obsidian-vault`
- standard-library logging only

Core now provides `core/connectors/boundary.py` as the composition boundary. The old `core/connectors/obsidian_connector.py` remains as a compatibility shim.

`runtime_api.py` now consumes the connector through `create_runtime_connectors()`.

## Validation

- DGM-MAT-Connectors: **2 passed**
- Connector/API/autonomy focused DGM-MAT suite: **8 passed**
- `python -m compileall -q core tests`: passed
- Full DGM-MAT suite: **100% passed**, ~70.94 s
- No GitHub Actions triggered
- FULL-MIRROR untouched

## Git

DGM-MAT-Connectors:
- `f4df495` — `feat(connectors): establish standalone Obsidian connector`
- `0c86139` — `chore(connectors): ignore Python caches`
- pushed to `main`

DGM-MAT Core connector changes are validated and ready for the next selective commit.

## Safety

No destructive deletion was performed. The Core connector implementation remains available through a compatibility shim, while the standalone package becomes the implementation authority.
