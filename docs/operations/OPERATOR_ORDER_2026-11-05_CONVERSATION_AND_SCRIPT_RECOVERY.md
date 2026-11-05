# Operator order — DGM-MAT autonomous recovery and repository consolidation

**Issued:** 2026-11-05  
**Authority:** Explicit operator instructions in DGM-MAT Fixing 21  
**Priority:** Immediate  
**Source of truth:** GitHub; all code, documentation, tests, PRs and branch reconciliation happen in GitHub first.

## Mission outcome

Leave DGM-MAT as the only application/agent intended to perform ongoing work on the PC. The PC is not to be used as the development workstation during this mission. Do not consume Desktop Commander quota for repeated inspection or development.

## Operating mode and local runtime

1. Do all development, code review, tests, documentation, PR creation and merges through GitHub.
2. Do not use Codex, Claude Code/FCC, Ollama, unrelated Windows services or background agents as active workers. Do not use paid APIs or paid credits.
3. The operator requested DGM-HUB to be stopped so only DGM-MAT remains active. Record this as a local shutdown action for the final, explicitly authorized PC deployment step. Do not pretend the Hub has been stopped from GitHub.
4. Important dependency: stopping DGM-HUB disables the current Kilo/LLM7 consultation bridge. DGM-MAT must continue standalone with its local mission engine and repository-learning capabilities; do not silently restart the Hub or substitute paid providers. Record any work that specifically requires Kilo/LLM7 as blocked until the operator later authorizes the Hub.
5. Give DGM-MAT only the access it needs to its designated project/worktree roots. Use least privilege. Before modifying an existing file, preserve a timestamped backup and record its SHA-256. Never grant blanket access to the entire Windows filesystem, browser profiles, credentials, security stores or unrelated user data.
6. Do not request the operator to approve a pop-up while away from the PC. If a platform-level authorization is required, record the exact blocked action and continue with GitHub-only work.
7. Desktop Commander is reserved for the final local sequence only: synchronize the approved GitHub branch (git pull), run the repository's supported installer/update script with its backup behavior, then launch the installed DGM-MAT executable. Do not use it for repeated scans, shell searches, process inventories or routine status polling.
8. The local shutdown sequence must stop only positively identified nonessential application processes/services (DGM-HUB, Claude/FCC, Ollama, Codex and other development helpers). Preserve Windows core services, security/antivirus, networking, display/input, Desktop Commander and DGM-MAT. Do not kill processes by broad name where ownership/path is ambiguous. If identity cannot be established, leave the process running and report it.
9. Do not stop DGM-HUB until the standalone DGM-MAT runtime has been validated and the operator's requirement to run DGM-MAT alone is met. Document the resulting loss of external Kilo/LLM7 help.

## Conversation and script recovery

1. Inventory all available conversation sources for ChatGPT, Grok and Gemini, distinguishing metadata-only records, complete transcript exports, partial sources and inaccessible sources.
2. The operator has now explicitly authorized DGM-MAT to capture real conversations from ChatGPT, Gemini and Grok through the already-authenticated browser UI, one conversation at a time. Use only normal rendered page content on explicit provider allowlists; do not inspect/export cookies, tokens, passwords, localStorage, IndexedDB, browser profile databases or authentication stores. Do not reverse-engineer hidden/private APIs, bypass CAPTCHA/MFA/paywalls/rate limits, send messages, edit/delete conversations or change account settings. If login/challenge/rate-limit or inaccessible content is encountered, stop that provider and record a precise blocker. This newer instruction supersedes the earlier export-only/no-logged-in-website restriction.
3. Preserve source archives and original files unchanged. Compute hashes and record source paths, sizes, timestamps and provider identity. Import copies only.
4. Parse supported JSON/HTML/text exports with the existing conversation-intelligence pipeline. Metadata is not a transcript.
5. Extract scripts/configurations with provenance: provider, conversation ID/title, source file, message/turn reference when available, language, project, purpose, date/version, dependencies, hash and extraction status.
6. Classify by project and technical purpose. Detect exact and near duplicates, compare variants, retain all original variants and never silently select a “best” version.
7. Build a searchable catalogue and project-specific inventories. Keep uncertain attribution/version explicitly unknown.
8. Produce resumable progress reports with mission ID, status, percentage, counts, errors, recovered artifacts, duplicate groups, blockers and next actions.

## GitHub branch and PR consolidation — operator-authorized

The operator explicitly authorizes integrating the useful work from old branches and deleting obsolete branches after reconciliation. This is not permission to discard unreviewed work.

1. Inventory every branch in the seven project repositories: DGM-MAT, DGM-MAT-Mobile, DGM-HUB, Office-Kit, VazaoSovereignTrader, VAZAO-EVSE-Platform and andreos-memory.
2. For every branch, compare against the current default branch and record ahead/behind commits, unique files, open PRs, CI checks and last activity.
3. Classify each branch as: already integrated/identical, safe stale branch, unique work to port, active work, duplicate PR/branch, or blocked by conflict/test/engineering gate.
4. Before removing any branch with unique commits, port the useful changes through a focused PR, run relevant tests and obtain successful required checks. Never merge solely because Git reports mergeable.
5. Preserve a recovery point for each branch whose content is being reconciled (GitHub backup ref/tag or a verified patch/archive in the recovery repository) until its content is proven present in the target branch.
6. Merge only after review, conflict resolution and required checks pass. Do not force-push protected branches.
7. After all unique content is integrated and verified, delete obsolete remote branches where the GitHub permissions/API support it. Keep each repository's default branch and any explicitly active branch. Do not delete a branch if its commits, PR, release, deployment or local-only work are not reconciled.
8. Produce a final branch ledger showing every original branch, destination commit/PR, backup reference, deletion status and reason. “All branches cleaned” is only valid when the ledger proves it.

## First DGM-MAT mission

Start a resumable, read-only mission with the goal:

> Inventariar fontes locais e capturar, através da interface autenticada do Chrome, conversas reais de ChatGPT, Grok e Gemini, uma a uma; preservar originais, checkpoint por conversa, importar para memória local e recuperar scripts/configurações com proveniência.

In parallel, prepare the GitHub branch ledger and focused PRs for useful unique work. The mission must checkpoint and resume; it must not wait for all exports to be present before cataloguing known sources.

## Safety and acceptance criteria

- Original conversation exports and scripts remain unchanged; recovered artifacts have provenance and stable fingerprints.
- Existing files are backed up before modification, with timestamp and SHA-256.
- No paid providers, paid APIs, credentials scraping or unauthorized account access.
- No broad filesystem permission grants or arbitrary OS/service changes.
- Every merged PR has an auditable review and successful required checks.
- Every deleted branch has a verified destination or is proven redundant/obsolete.
- A real mission ID and durable checkpoint exist; queued work is not completion.
- Reports clearly separate completed work, blocked work and unknowns.
