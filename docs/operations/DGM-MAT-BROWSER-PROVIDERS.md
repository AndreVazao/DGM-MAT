# DGM-MAT — Authenticated browser AI providers

## Primary provider set

The browser recovery and consultation architecture uses the following primary web services:

| Provider | Official browser host | Initial recovery adapter |
|---|---|---|
| ChatGPT | `chatgpt.com` | Existing |
| Grok | `grok.com` and the Grok route on `x.com` | Existing |
| Gemini | `gemini.google.com` | Existing |
| DeepSeek | `chat.deepseek.com` | Integrated in the browser mission operator |
| Qwen | `chat.qwen.ai` | Integrated in the browser mission operator |

Other genuinely free web AI services can be optional secondary consultation sources. They do not replace these five primary providers or introduce paid API dependencies.

## Two separate capabilities

1. **Historical recovery** discovers visible conversation links, opens one conversation at a time, reads rendered messages, and saves immutable local captures. It is read-only.
2. **AI consultation** is a separate workflow that previews a minimal prompt, obtains explicit authorization to send it through the normal provider UI, captures the visible answer, and records provenance. Historical recovery must never send messages.

## Provider adapter rules

- Use the user's existing authenticated browser session and ordinary rendered UI only.
- Do not read cookies, tokens, browser databases, hidden/private APIs or network internals.
- Do not bypass login, MFA, CAPTCHA, rate limits or usage limits.
- Detect provider login/challenge/quota states and pause that provider. Resume only when the user/service permits it.
- Provider selectors and URL route shapes are heuristics until validated against the user's current UI. Unknown IDs/roles and DOM mismatches must fail closed or remain partial.
- A rendered DOM top is not proof of the provider's oldest conversation message. Full-history status requires explicit provider-specific boundary evidence.
- Keep provider identity, conversation ID, URL, capture time, adapter version, message order, completeness and content fingerprints.
- No paid API fallback, subscription action, API key creation or account billing.

## DeepSeek and Qwen route recognition

The first adapter recognizes current route patterns and common conversation query parameters:
- DeepSeek: `/a/chat/s/<conversation-id>`, `/chat/s/<conversation-id>`, or a recognized conversation ID query parameter.
- Qwen: `/chat/<conversation-id>`, `/c/<conversation-id>`, `/conversation/<conversation-id>`, or a recognized conversation ID query parameter.

These patterns are discovery hints, not claims that every account/session uses the same route. If the actual authenticated UI differs, the adapter records no ID and waits for a verified selector/route update.

## Acceptance before enabling

For each of the five primary providers, test with the user's authenticated session:
- discover the sidebar list and report the number of visible conversations;
- open one known conversation and compare visible message count/order against the page;
- scroll through virtualized history and verify overlap/deduplication;
- stop on login challenges, quota warnings or unexpected UI;
- confirm raw and normalized copies exist in the configured persistent Vault;
- resume after interruption without losing checkpoints;
- never claim complete history when the oldest boundary is unknown.

The DeepSeek and Qwen adapters must remain disabled for unattended recovery until these checks pass on the real browser sessions.
