# Operator order — conversation and script recovery

**Issued:** 2026-11-05  
**Authority:** Explicit operator instruction in the DGM-MAT Fixing 21 session  
**Priority:** High — begin as soon as the runtime and required providers are verified  
**Execution mode:** DGM-HUB Respond; DGM-MAT may ask for external assistance when blocked

## Objective

Make DGM-MAT recover and organize the user's prior engineering and development knowledge from locally available, user-authorized conversation exports and machine-readable activity sources. The result must be a searchable, traceable catalogue of reusable scripts, code snippets, configurations, decisions and project context.

## Ordered work

1. Verify DGM-MAT API, queue worker, repository-learning worker, DGM-HUB bridge and provider availability before dispatch. Record timestamps and evidence.
2. Confirm DGM-HUB is in **Respond** mode for DGM-MAT. Use only the free providers **Kilo** and **LLM7** for help-seeking. Ask both when a material technical blocker cannot be resolved internally; preserve the prompt, provider/model, response, timestamp and the decision taken. Record disagreement rather than silently selecting an answer.
3. Discover all available conversation sources for ChatGPT, Grok and Gemini. Report separately:
   - metadata-only sources;
   - complete transcript exports;
   - partial or inaccessible sources;
   - official export archives not yet supplied or not yet found.
4. Search only user-accessible local folders and explicitly authorized exports for official ChatGPT, Grok and Gemini exports. Do not scrape logged-in websites or access browser cookies, tokens, private sessions, passwords or authentication stores.
5. Preserve source archives and original files unchanged. Compute hashes, record source paths, sizes, timestamps and provider identity. Import copies only.
6. Parse supported JSON/HTML/text exports with the existing conversation-intelligence pipeline. Do not claim a source is fully ingested merely because metadata was discovered.
7. Extract code and configuration artifacts with provenance: provider, conversation ID/title, source file, message/turn reference when available, language, project, function, date/version, dependencies, hash and extraction status.
8. Classify artifacts by project and technical purpose. Detect exact and near duplicates, compare variants, and retain every original variant. Never overwrite a project file or silently choose a “best” version.
9. Build a searchable catalogue and project-specific inventories. Include unresolved project attribution and uncertain versions as explicit unknowns.
10. Produce a progress report with mission ID, status, percentage, counts, errors, provider consultations, source coverage, artifacts recovered, duplicate groups, pending approvals and next actions. Save reports under the DGM-MAT reports/diagnostics area and sync them through a reviewable Git branch/PR.

## Safety and approval boundaries

- Discovery, hashing, parsing copies, classification, comparison and reporting are read-only with respect to source material.
- Never delete, move, rename or modify original exports or source conversations.
- Never overwrite existing scripts or configurations. Preserve recovered material in a separate archive/catalogue area.
- No commit to protected/main branches, merge, force-push, branch deletion, installation, paid service, API purchase or external message without explicit operator approval.
- Do not enable Codex, Claude/FCC, Ollama or paid providers. Do not consume paid credits. The permitted help-seeking providers for this order are Kilo and LLM7 only.
- If an official export is absent, request the export from the operator; do not infer full conversation contents from metadata.
- If authentication, provider connectivity, a missing export or a permission boundary blocks progress, record **BLOCKED** with exact evidence and continue with independent read-only tasks.
- Do not report completion from a queued mission, a metadata count, or a successful standalone provider test. Completion requires persisted results and evidence.

## First mission

Start a read-only mission with the goal:

> Inventariar as fontes locais de conversas ChatGPT, Grok e Gemini, verificar a disponibilidade de exportações oficiais e preparar a recuperação catalogada de scripts e configurações sem alterar os originais.

The mission must checkpoint progress and be resumable. It must not wait for all sources to be present before cataloguing the sources already available.

## Acceptance criteria

- A real mission ID exists and its state/progress is read from the durable checkpoint and queue.
- DGM-HUB Respond mode and Kilo/LLM7 consultation capability are evidenced.
- Source coverage distinguishes metadata from complete transcript content.
- Every recovered artifact has provenance and a stable fingerprint.
- Originals remain unchanged.
- A report identifies completed work, blockers and the next safe action.
