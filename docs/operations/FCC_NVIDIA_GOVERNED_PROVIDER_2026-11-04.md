# Governed FCC / NVIDIA NIM Provider

Date: 2026-11-04
Branch: `feat/governed-fcc-nvidia-provider-2026-11-04`
Base: `origin/main` at `15bb5704fefb297b55e5cab8e88334162a3419be`

## Why this adapter exists

The existing ChatGPT, Claude, Gemini and Grok provider classes are placeholders. The provider registry only activates Ollama by default. The PC currently has no Ollama listener and only 0.76 GB physical memory available, below the Ollama adapter's 1.25 GB minimum.

The installed Free Claude Code (FCC) server is configured with NVIDIA NIM and the model `nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b`. NVIDIA currently lists this model as a Free Endpoint. The hosted API remains subject to NVIDIA API Trial Terms, quotas and rate limits; this is not unlimited compute. See:
- https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b
- https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-super-vl-120b-a12b

## Current PC configuration observed

- FCC server version: 6.10.4.
- Active provider in FCC configuration: `nvidia_nim`.
- Default model route: Nemotron 3.5 Super VL.
- Other remote provider credentials were reported missing.
- FCC was observed listening on `0.0.0.0:8082`.
- The earlier local inspection reported proxy authentication disabled / no usable strong proxy token.
- Plain `claude auth status` reported no first-party Claude login.
- Ollama port 11434 was closed; free physical memory was approximately 0.76 GB.
- The FCC server was started temporarily for read-only inspection and then stopped. No inference request was sent and no provider quota was consumed.

The current FCC configuration is unsafe for DGM-MAT integration. The adapter must refuse it.

## FCC API contract verified against upstream source

The current FCC implementation:
- exposes `GET /admin/api/config` and `GET /admin/api/status` to loopback clients;
- reports active bind host, port, provider, model and provider credential status in `/admin/api/status`;
- stores the API proxy token in `ANTHROPIC_AUTH_TOKEN` (blank means no API authentication);
- masks secret values in the Admin config response;
- protects `GET /v1/models` and `POST /v1/messages` through the same API-key dependency;
- exposes configured model routes as gateway IDs such as `anthropic/{provider/model}` and `claude-3-freecc-no-thinking/{provider/model}`;
- uses `MODEL_OPUS`, `MODEL_SONNET` and `MODEL_HAIKU` as optional tier overrides, rather than a `MODEL_FALLBACKS` field.

Source inspected: https://github.com/valorisa/Free-Claude-Code (admin_routes.py, admin_config/manifest.py, admin_config/status.py, admin_config/values.py, dependencies.py, routes.py and model_catalog.py).

## Adapter contract

`FccNvidiaProvider` is default-off and is registered only when `DGM_FCC_NVIDIA_ENABLED=1`.

Before it reports healthy, it verifies:
1. DGM connects only to a plain HTTP loopback URL.
2. FCC's configured bind host and active server host are loopback; `0.0.0.0` is rejected.
3. Active server port matches the endpoint used by DGM-MAT.
4. A strong 24+ character token exists in the DGM-MAT credential vault under provider `nvidia_nim`, credential type `api_key`.
5. Unauthenticated `GET /v1/models` returns HTTP 401/403, proving that FCC API authentication is actually enforced.
6. The vault token is accepted by authenticated `GET /v1/models`, and the expected gateway model ID is advertised. These requests do not run inference.
7. The active FCC provider is `nvidia_nim`, and its configured and active model match the allowlist.
8. Optional Claude tier routes (`MODEL_OPUS`, `MODEL_SONNET`, `MODEL_HAIKU`) are blank or use the same allowlisted model.

The adapter exposes only text chat through the Anthropic-compatible `/v1/messages` endpoint. It does not expose shell, filesystem, browser, tools or function calling. Redirects are blocked, inputs are capped at 8,000 characters, responses at 16,000 characters, and unknown provider options are rejected.

## Local usage budget

A persistent SQLite budget applies per UTC day:
- 5 requests/day maximum.
- 25,000 reserved tokens/day maximum.
- 4,096 tokens reserved for each request.
- 2,048 maximum output tokens per request.
- 2 concurrent requests maximum.
- No paid fallback, automatic provider switch or retry to another model.

These are DGM-MAT local safety limits, not a claim about NVIDIA's account-specific quota. A failed/timeout request consumes the local reservation conservatively.

## Activation procedure — intentionally not performed

1. Change FCC bind host to `127.0.0.1`, port 8082.
2. Set a strong FCC `ANTHROPIC_AUTH_TOKEN` (24+ characters).
3. Store the same token in the DGM-MAT vault using the existing provider credential contract.
4. Keep `MODEL` on the verified Nemotron model; leave tier overrides blank or set them to the same allowlisted model.
5. Start FCC on demand.
6. Set `DGM_FCC_NVIDIA_ENABLED=1` for the DGM-MAT runtime only after the above checks pass.

The environment flag is not set by this PR. No service was restarted and no provider call was made.

## Remaining work

This PR makes the governed provider available as a default-off capability. It does not yet connect model output to code changes or MissionEngine. The next implementation must:
- use the provider only through `GovernedProviderService`;
- ask for a bounded unified diff, never tools or shell access;
- validate and apply the diff only inside a registered worktree;
- run the fixed pytest validation command;
- retain the worktree and evidence until independent QA and human integration approval.
