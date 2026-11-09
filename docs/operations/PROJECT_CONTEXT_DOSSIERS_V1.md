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
