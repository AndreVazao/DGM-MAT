# DGM-MAT — Mobile Chat, History Search and Session Scopes

**Date:** 2026-11-08  
**PR:** #285  
**Base:** `main` at `c009c512593f16ee1bf085012fa700e4352433fe`

## Purpose

Make the Android mobile client a least-privilege client of the PC brain, provide bounded search across durable mobile threads, and preserve the desktop cockpit's operator session without giving a paired phone general operator authority.

## Pairing contract

Remote `POST /auth/pair` accepts only:
- `dgm-mat-mobile-android`
- `dgm-mat-mobile-web`
- `dgm-mat-chrome-extension`

A desktop cockpit identity is not accepted through remote pairing. The PC cockpit obtains its operator session only through the loopback-only bootstrap exchange `POST /auth/session`.

Mobile sessions receive:
- `local-client`
- `mobile-read`
- `mobile-chat`
- `mobile-maintenance`

They do **not** receive `operator`. Operator sessions remain a superset of the three mobile scopes for compatibility with the PC cockpit and local administration. Mobile sessions cannot use general operator routes.

## Route boundaries

- `mobile-read`: bounded thread search, imported recovery search and message reads, workspace scan, approvals and action-queue read views.
- `mobile-chat`: create/rename threads, post chat messages and request capability discovery. MissionEngine approval rules remain authoritative.
- `mobile-maintenance`: explicit USB/ADB diagnosis and allowlisted repair routes.
- Existing read-only `local-client` routes remain available to the paired mobile session.
- Browser extension sessions retain their independent browser-capture scope.

## Local thread search

`GET /mobile/threads/search?q=<term>&limit=25`

- Query: 2–200 non-space characters.
- Limit: 1–50.
- Case-insensitive matching across thread title, project, repository and message content.
- Returns one result per matching thread, with a bounded snippet and metadata only; never returns the full transcript.
- Results are ordered by most recently updated thread.
- Search is local and does not call any external provider.

The existing `GET /recovery/search` remains the bounded imported archive search. It searches source metadata and indexed ChatGPT message text under its existing scan limits. Full imported message reads remain bounded and integrity-checked. This does not imply that every provider archive has complete message-text indexing.

## AI readiness and credentials

The mobile bridge reports `api_status` separately from `ai_ready` and `ai_mode`. Its top-level `status` is `degraded` when the API is healthy but neither Ollama nor a governed provider is available; an Ollama endpoint with zero installed models is not counted as AI-ready. A healthy HTTP API is not proof that an LLM provider is registered, configured, within quota or able to answer. Mobile and PC cockpit UIs now display this distinction.

Ordinary mobile LLM chat remains explicit opt-in:
- `DGM_MOBILE_GOVERNED_CHAT_ENABLED=0` by default.
- `DGM_FCC_NVIDIA_ENABLED=0` by default unless the operator has configured and verified the local FCC/NVIDIA NIM bridge.
- No automatic Ollama startup unless its existing explicit mode is set.
- No paid fallback, tools, shell, mission execution or hidden provider endpoints in the chat-only inference path.

The existing `CredentialVault` stores its Fernet master-key file beside the encrypted credential file. Do not expose provider API-key write forms through the dashboard until the master key is protected by Windows DPAPI/Windows Credential Manager and migration/rollback tests exist. The current cockpit bootstrap prompt only exchanges the local bootstrap credential for a short-lived session; it does not collect provider API keys.

## Validation and acceptance

Latest CI on the reviewed backend head:
- Focused PR Validation: success — run 42509402563.
- Chrome Extension Validation: success — run 42509402174.
- Windows installer digest gate: success.
- Windows Executable Build #325: **SUCCESS**, run 42510552509, built from reviewed code/test head `1118660af94a9255786691cf6d51d75c22a046fb`.
- Artefacto Windows atual: `DGM-MAT-Windows-3.12-dca47d0`, 111,221,551 bytes; SHA-256 do ZIP exterior GitHub `e1db00d4e4e71b7733867be5a28d861d0c133670b0807cef62d2278f2e16a7c3`; expira 2027-02-06 18:32:55 UTC.
- Download: https://github.com/AndreVazao/DGM-MAT/actions/runs/42510552509/artifacts/13629805705.
- O digest acima é do ZIP exterior; o EXE deve continuar a ser validado pelo sidecar `publish/DGM-MAT.exe.sha256` no artefacto extraído.
- Snyk private tests: quota exhausted; no clean Snyk result is claimed.

- Focused PR Validation covers mobile pairing, scope inheritance, route classification and thread search.
- Chrome Extension Validation also runs the shared auth regressions.
- Windows executable build validates packaging; it is not local Windows 10 acceptance.
- Mobile APK and PC cockpit PRs depend on this backend contract.
- Still required: install the APK on the Android device, pair against the actual PC backend, verify mobile-read/mobile-chat/mobile-maintenance route behavior, run a real governed free-provider conversation, and confirm no operator access from the phone.

**No runtime flags are enabled by this PR. No secrets are added. No local PC or phone is modified.**


### Atualização final de build — 2026-11-08 18:28 UTC
- Focused PR Validation run 42509849814: SUCCESS.
- Chrome Extension Validation run 42509849817: SUCCESS.
- Windows Executable Build run 42509849909: SUCCESS; artefacto e SHA-256 documentados acima.
- O novo teste integrado confirma pairing mobile real no TestClient loopback, criação de thread, envio de mensagem, pesquisa de histórico e negação de catálogo de comandos/missões para a sessão mobile.
- Build Windows é evidência de packaging CI, não aceitação local Windows 10.


### Atualização provider readiness — 2026-11-08 18:33 UTC
- `governed_chat_status()` agora atualiza observações de saúde ausentes/antigas quando `DGM_MOBILE_GOVERNED_CHAT_ENABLED=1` está explicitamente ativo.
- A verificação é limitada por janela de 30 s para tentativas e 60 s para observação; executa apenas `check_health()`, nunca uma conclusão/chat completion.
- Com a flag desligada, não inicializa nem consulta providers. Testes verificam ambos os casos.
- Focused PR Validation #42510552602: SUCCESS.
- Chrome Extension Validation #42510552584: SUCCESS.
- Windows Executable Build #42510552509: SUCCESS; artefacto atual documentado acima.
