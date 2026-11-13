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
- Up to ten most recently updated pull requests and ten issues (excluding pull requests), including number, title, state, timestamps, labels and GitHub URL. Closed records are retained as historical evidence.

The check-run query is not a claim that the repository's default branch is at
the local HEAD. It asks GitHub for checks attached to the exact commit SHA
recorded by the local inventory. A missing check run does not mean tests passed.

## Safety and limits

- GET requests only; no branch, issue, pull request, workflow or repository
  mutations.
- At most four requests per uncached dossier read (repository metadata, optional exact-SHA checks, pull requests and issues); five-second default timeout,
  no redirects, 20 check-run result cap and a five-minute process-local cache.
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

## Pull request and issue history

Pull requests and issues are queried separately with `state=all`, sorted by
most recently updated, capped at ten records each. GitHub's issues endpoint
also returns pull requests; those entries are explicitly filtered out of the
issue collection to prevent double counting. Only bounded metadata is stored
in the dossier projection: no discussion comments, review bodies, issue bodies,
or user account details are fetched.

A failed collection produces a partial activity status and does not erase
repository metadata or the other successful collection. The result is a recent
activity window, not a complete archive of every historical PR or issue.
