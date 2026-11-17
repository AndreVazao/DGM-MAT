# Project dossier evidence freshness

The project dossier reports source timestamps independently so the operator can judge evidence age without conflating different sources.

## Fields

- `generated_at`: UTC timestamp for the dossier response.
- `evidence_freshness.latest_conversation_capture_at`: newest conversation capture timestamp included in the bounded dossier projection.
- `evidence_freshness.latest_vault_snapshot_at`: newest repository tree snapshot timestamp.
- `evidence_freshness.latest_static_audit_at`: timestamp recorded by the latest accepted static audit.
- `evidence_freshness.repositories[]`: per exact-path-matched repository inventory timestamp, scan status, tree generation timestamp, GitHub observation timestamp/status and exact checked commit SHA.

## Interpretation and safety

These timestamps describe separate observations. They do not imply that the local repository, GitHub default branch, runtime, provider conversation archive or project is current. A persisted inventory timestamp is not a live filesystem probe; a GitHub observation is not a local Git refresh; a CI check on an exact SHA is not runtime acceptance.

No age threshold is applied. Consumers must display the timestamps and statuses rather than silently upgrading old evidence to current or complete. Unmatched repositories are not inferred from similar names or URLs.

The endpoint remains read-only and does not return transcript bodies, credentials or private Vault content.
