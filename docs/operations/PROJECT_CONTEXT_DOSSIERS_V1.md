# Project context dossiers V1

## Purpose

Build evidence-linked Markdown context dossiers from completed conversation
intelligence snapshots. This is a downstream read-only projection: it does not
change provider accounts, original exports, raw archives, or the SQLite source
records.

## Current contract

- Input: `ConversationProgressStore` rows with status `complete` and a valid
  conversation snapshot.
- Project assignment: exact operator-supplied mapping keys in the form
  `provider:conversation_id`. There is no title matching, fuzzy classification,
  or inferred cross-project association.
- Unmapped and incomplete conversations are counted, not silently assigned.
- User-role messages are shown as user statements/evidence, not automatically
  certified as current requirements or approved decisions.
- Assistant/model messages are shown separately as proposals/output and never
  promoted to accepted decisions.
- Extracted code is included with its fingerprint and source conversation.
  Repository presence, correctness, acceptance, and recovery are not asserted.
- Generated Markdown is written atomically. A content-addressed history copy and
  JSON source manifest are retained. Source snapshots and original archives are
  not modified.

## Output

For each explicitly mapped project:

- `<output-root>/<project-key>/PROJECT_CONTEXT.md`
- `<output-root>/<project-key>/manifest.json`
- `<output-root>/<project-key>/history/<sha256>.md`

The dossier contains coverage, user statements, assistant proposals, extracted
code candidates, decision safeguards, unresolved-review notes, next actions, and
a source manifest.

## Deliberate limitations

V1 does not infer project mappings, parse decision acceptance from conversational
phrasing, merge conflicting requirements, inspect Git repositories, verify
candidate code against files, or claim provider archive completeness. Those are
separate evidence-producing stages. Repository/branch/commit/test state must be
added only from a live inventory tied to a commit SHA. A user-approved mapping
workflow and a separate decision-review record are required before a dossier can
be considered authoritative.

## Safety

Project keys are validated against path traversal. Writes use a temporary file
in the destination directory followed by atomic replacement. History filenames
are SHA-256 content-addressed. The generator does not delete or rewrite source
records.


## Bounded-memory and provenance hardening

The follow-up implementation adds a SQLite iterator based on `fetchmany(batch_size)`.
The dossier generator defaults to batches of 10 records (configurable from 1 to
100), decodes one conversation snapshot at a time, and makes separate bounded
passes for coverage, user messages, assistant messages, artifacts, and source
manifest IDs. It writes the Markdown to a temporary file incrementally, hashes
it in 1 MiB chunks, copies the content-addressed history file incrementally,
and atomically replaces the current dossier. It does not build a project-wide
list of snapshots, messages, artifacts, or source IDs.

The explicit memory guarantee is therefore: SQLite page of at most
`batch_size` result rows plus one decoded conversation snapshot and the
current message/artifact being rendered. A single exceptionally large
conversation or code artifact is still decoded as one JSON value and is not
bounded independently; splitting source snapshots into message-level rows is
a separate future migration. The generator reports this exact limitation and
does not claim a hard process-RAM ceiling.

Rendered message evidence now includes timestamp, source path, and serialized
message metadata when supplied. Code candidates retain source message ID,
artifact source fingerprint, source path and source URL when available; absent
fields are explicitly marked unavailable. No provenance is fabricated.

The manifest streams source IDs into JSON rather than retaining a potentially
large array in memory. Schema version is 2. The source SQLite database and
original archive remain read-only throughout generation.


## Read-only Vault dossier query API — V1

The repository-learning API now exposes:

- `GET /runtime/repository-learning/dossier?project_id=<registered-vault-project>`
- Optional bounded parameters: `conversation_limit` (1–500), `snapshot_limit` (1–100), and `finding_limit` (1–200).
- Route scope: operator session only. It is explicitly classified in the API security inventory.
- Response includes canonical project identity/aliases, conversation counts grouped by provider and completeness, a bounded list of conversation metadata with evidence references, repository tree snapshot metadata, and the latest valid Vault static-audit summary/findings when available.
- Transcript bodies, raw archive bytes, credentials, and full message contents are never returned.
- The endpoint reports only conversations already assigned to the project in Vault. It does not infer assignments, provider archive completeness, Git branch/commit, runtime health, test success, implementation completion or operator decisions.
- The latest static audit is read only from the project's Vault audit directory, with path containment, symlink exclusion, JSON size bounds and project identity checks.
- Empty or incomplete evidence is represented explicitly (`no_evidence`, `evidence_partial`, completeness `unknown`); absence is not converted into a claim that a provider or repository has no history.

This is the first queryable dossier projection, not the final natural-language project consultation. GitHub branch/PR/issue/CI evidence, local runtime probes, explicit decision records, provider source checkpoints and conversation-to-code links remain separate integration stages.

- The dossier also exposes GitHub repository URLs extracted from assigned Vault conversations, including verification state and exact message provenance, plus extracted code-artifact metadata/fingerprints linked to the source conversation. These remain unverified candidates until matched to a repository file/commit; code bodies are not returned.


## Exact-path local Git evidence integration

The operator dossier endpoint now includes the persistent repository-learning observation
when (and only when) the Vault project's canonical `repository_path` matches an
inventory record by normalized absolute path. The projection exposes the observed
branch, HEAD SHA, dirty flag, scan status/error, last-seen timestamp and tree artifact
fingerprint/metadata.

Repository name similarity, remote origin, aliases and heuristic project groups are
not used to claim identity. An unmatched path is reported as
`no_exact_path_match`, not as proof that the project repository is absent.

Important freshness rule: these fields are the last persisted repository-learning
observation, not a live Git command. The dossier labels that distinction explicitly;
a future live probe must be a separate, bounded evidence source. The API remains
read-only and returns no source file contents or secrets.


## Natural-language project resolution — V1

The same operator-only dossier endpoint also accepts `query=<natural-language request>`
instead of `project_id`. Resolution is based exclusively on complete, case-insensitive
project names, IDs and registered aliases with identifier boundaries. It does not
use fuzzy similarity, repository names, remote URLs or inferred project groups.

- Exactly one Vault project match returns its dossier and a `resolution.status=resolved`
  record containing the matched project and alias evidence.
- Multiple project matches return `status=ambiguous` with the candidate IDs/names;
  no dossier is selected and no project is guessed.
- No match returns `status=not_found`.
- Supplying both selectors, or neither selector, is rejected.
- Query length is bounded to 2–300 characters. Existing dossier result limits and
  operator authentication remain in force.
- This endpoint is a backend capability. The desktop chat has not yet been wired
  to invoke it automatically; that is a separate UI integration and end-to-end step.
