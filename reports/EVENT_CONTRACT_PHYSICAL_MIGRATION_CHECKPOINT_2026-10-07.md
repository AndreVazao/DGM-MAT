# Event Contract Physical Migration Checkpoint — 2026-10-07

## Gate

The first contract-backed physical migration step after the green regression baseline is the canonical event model boundary.

## Change

`DGM-Contracts` now exposes `Event`, a compatibility-preserving event contract derived from `EventEnvelope`.

Compatibility details:
- accepts legacy `id` input through Pydantic validation alias
- canonical field remains `event_id`
- legacy `event.id` property remains available
- full event payload/trace/TTL/ecosystem fields remain contract-owned

DGM-MAT `shared.models.event` is now only a compatibility shim importing `Event` from `dgm_contracts`.

This establishes the direction:

`Core/Cockpit/Agents -> public contract -> DGM-Contracts`

instead of treating `shared.models.event` as an internal authority.

## Validation

DGM-Contracts:
- `python -m pytest -q` -> **4 passed**

DGM-MAT focused gate:
- contracts + autonomy + runtime + knowledge -> **all passed**

DGM-MAT full suite:
- `python -m pytest -q` -> **100% passed**
- runtime approximately 65 seconds

No GitHub Actions dispatch was used.

## Physical extraction decision

The event contract migration is accepted as the first physical boundary step. The full `DGM-MAT-Agents` extraction is **not yet authorized** because several agents still depend directly on Core-owned logging/provider/task services. Their dependency rewrite must be completed before moving their files.

The next extraction gate is therefore:

1. finish agent public dependency adapters;
2. copy Agents into `DGM-MAT-Agents` without deleting Core source;
3. install/test the satellite independently;
4. rewrite Core consumers to the public agent boundary;
5. run full local regression;
6. only then remove migrated source from DGM-MAT.

## Safety

- `DGM-MAT-FULL-MIRROR` untouched.
- No destructive source deletion.
- No force-push.
- GitHub Actions remains manual-only.
