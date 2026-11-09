# GitHub repository reference verification

DGM-MAT extracts canonical `github.com/{owner}/{repository}` links from conversation titles and messages when a conversation is archived. The source conversation and provenance remain in the local Vault.

## Automatic verifier

The API starts a small daemon worker by default. It waits 15 seconds after startup, then checks at most five pending references per cycle and waits 30 minutes before the next cycle. Every check uses the public unauthenticated GitHub REST endpoint:

- No GitHub token, Authorization header, provider cookie, or browser session is used.
- Only the repository owner/name is sent to `api.github.com`; conversation text and provenance are never sent.
- Per-request timeout is five seconds.
- A batch is capped at ten even if configuration is changed.
- The worker is non-blocking, logs failures, retries on a later cycle, and stops with the API.
- It never changes or deletes the archived conversation.

## Configuration

| Environment variable | Default | Bounds / meaning |
|---|---:|---|
| `DGM_GITHUB_REFERENCE_VERIFIER_ENABLED` | `1` | Set to `0`, `false`, `no`, or `off` to disable |
| `DGM_GITHUB_REFERENCE_VERIFIER_INTERVAL_SECONDS` | `1800` | Clamped to 300–86400 seconds |
| `DGM_GITHUB_REFERENCE_VERIFIER_BATCH_SIZE` | `5` | Clamped to 1–10 references per cycle |

Manual operation remains available through `POST /recovery/github-references/verify?limit=10`.

## Meaning of statuses

- `verified_public`: GitHub returned the matching public repository metadata.
- `not_found_or_private`: GitHub returned 404. This does **not** prove that a repository never existed; it may be private, deleted, renamed, or inaccessible.
- `rate_limited`: GitHub rejected the request due to rate limiting; a later cycle can retry.
- `unavailable`: timeout, network/API failure, or unexpected metadata; a later cycle can retry.
- `pending_verification`: not yet checked.

New links are indexed automatically when archived. Existing Vault conversations still require a bounded `POST /recovery/github-references/reindex` backfill before they enter verification. Historical ChatGPT recovery-ledger archives have a separate paginated reindex path.

The verifier is intentionally not a GitHub repository crawler: it verifies only repositories already referenced in archived conversations.
