# Live GitHub evidence in project dossiers

## Scope

The dossier may enrich an exact local repository match with a bounded, read-only
GitHub observation. The integration accepts only canonical `github.com/owner/repo`
origins from the repository-learning inventory. It does not search GitHub by
project name, infer identity from aliases, or follow redirects.

## Data collected

- Repository identity, URL, default branch, archived/visibility state, and
  GitHub `pushed_at` / `updated_at` timestamps.
- Up to 20 check runs for the exact 40-character local HEAD SHA, with names,
  status/conclusion, timestamps, app slug and result URL.
- Observation timestamp and explicit availability/error classifications.

The check-run query is not a claim that the repository's default branch is at
the local HEAD. It asks GitHub for checks attached to the exact commit SHA
recorded by the local inventory. A missing check run does not mean tests passed.

## Safety and limits

- GET requests only; no branch, issue, pull request, workflow or repository
  mutations.
- At most four requests per uncached dossier read; five-second default timeout,
  no redirects, 20 check-run result cap, ten PR/issue item caps per collection, and a five-minute process-local cache.
- Uses an existing `GITHUB_TOKEN` environment variable when present; otherwise
  public GitHub repositories can be queried anonymously. No token is returned
  or logged by this component.
- HTTP failures, rate limits, private/unavailable repositories and malformed
  responses are represented as unavailable/partial evidence, never as success.
- Local branch, commit and dirty state remain persisted local observations.
  GitHub metadata is separately timestamped live evidence. Neither source
  replaces the other.
- This integration does not contact CI providers other than GitHub's check-runs
  API, execute code, download artifacts, or assert overall project completion.

## Current open work items

The live evidence collector also returns at most ten most recently updated open
pull requests and ten open issues. The GitHub issues endpoint can include pull
requests; those entries are explicitly excluded from the issue list to avoid
double counting. Only number, title, state, update timestamp, URL, draft state
(for PRs), and up to ten label names are retained. Bodies, comments, patches,
reviews, and conversation content are never fetched.

These are bounded returned items, not complete histories and not authoritative
total open counts. If either endpoint is unavailable or rate-limited, that
section is marked unavailable and the overall observation becomes partial.
