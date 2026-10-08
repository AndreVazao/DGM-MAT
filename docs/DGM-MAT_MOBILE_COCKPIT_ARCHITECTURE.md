# DGM-MAT Mobile Cockpit Architecture — 2026-10-08

## Decision

The mobile cockpit is a first-class DGM-MAT interface, not a separate intelligence system.

The required UX is a continuous conversation:

- thread history;
- new conversation;
- rename;
- project/repository context;
- natural free-form messages;
- visible understanding of intent;
- inline operational state;
- offline queue;
- automatic reconnect;
- same thread after reconnect.

## Canonical topology

MOBILE PWA
  -> Vercel public discovery
  -> Tailscale private HTTPS
  -> DGM-MAT API on authorized PC
  -> MobileConversationService
  -> intent layer / mission system / provider fabric
  -> local storage + AndreOS memory

Vercel is discovery/control-plane only.

Tailscale is the private transport.

DGM-MAT PC is the execution authority and conversation source of truth.

## Current implementation

DGM-MAT:

- core/mobile_runtime/models.py
- core/mobile_runtime/store.py
- core/mobile_runtime/intent.py
- core/mobile_runtime/service.py
- core/api/mobile_bridge.py
- core/api/api_server.py

Mobile repository:

- web/index.html
- web/styles.css
- web/app.js
- web/manifest.json
- web/sw.js

Capabilities:

- durable conversation threads;
- automatic first-message title suggestion;
- explicit rename;
- intent classification;
- project/repository hints;
- approval flagging for destructive/publication intent;
- offline local queue;
- reconnect replay;
- local PWA cache;
- Vercel discovery;
- Tailscale direct connection.

## Intent model

The first layer is deterministic and cheap.

Supported intent families:

- chat;
- status;
- audit;
- repair;
- implement;
- sync;
- research;
- memory;
- deploy.

This layer is deliberately independent of an LLM. A local LLM may enrich the response later, but it must never be the only mechanism needed to understand operational commands.

## Low-memory policy

The current PC is a Fujitsu Siemens ESPRIMO Mobile V6535 with:

- 2 logical CPUs;
- approximately 3.0 GB physical RAM.

Ollama is installed and contains useful small models, but a real generation test showed that qwen2.5:1.5b requires about 990.7 MiB while only about 831.7 MiB was available at test time.

Therefore DGM-MAT must not automatically load local models on this hardware.

The local LLM path is resource-gated. On a future stronger PC it can be re-enabled automatically after a real benchmark.

This is an evidence-based hardware policy, not a permanent architectural limitation.

## Reuse findings

The older devops-god-mode repository contains valuable historical cockpit work:

- continuous operator conversation UX;
- thread list and rename;
- mobile/offline queue;
- runtime snapshot sync;
- Ollama local-brain policy;
- multi-AI conversation intake;
- PC/mobile pairing;
- operator chat runtime.

It is treated as a reference/source for capability acquisition.

It is NOT a runtime dependency of DGM-MAT.

The current DGM-MAT implementation rebuilds the useful contract under DGM-MAT ownership.

DGM-Cockpit-Frontend currently has no implementation and remains a separate empty repository until a deliberate consolidation decision is made.

## Tailscale

The current PC identity is:

- hostname: PC-Vazao-Anjos
- DNS: pc-vazao-anjos.taild7e42f.ts.net
- IPv4: 100.69.225.47

Tailscale Serve is the intended secure HTTPS bridge from the mobile PWA to localhost:8181.

The tailnet currently reports Serve as disabled and provides a one-time administrator approval URL. Until that approval, no claim is made that mobile HTTPS access is operational.

## Vercel rendezvous

The existing dgm-mat-rendezvous service remains the control plane.

The DGM-MAT API now refreshes its rendezvous registration every 60 seconds with a 180-second TTL, so the mobile PWA can discover a live PC without manual IP entry.

The DGM-MAT-Mobile PWA is also linked to a dedicated Vercel project named dgm-mat-mobile with automatic GitHub main deployments. Vercel SSO protection is disabled for this public mobile shell.

A minimal public discovery mode was added for the PWA. It exposes only:

- node identity;
- node name/type;
- Tailscale endpoint;
- capabilities;
- version;
- last_seen.

No secret or conversation content is exposed.

## Future PC

When the stronger PC arrives:

1. re-run hardware inventory;
2. benchmark all installed Ollama candidates;
3. enable the local model route;
4. select models by task;
5. move heavier cognition locally where it improves latency/cost;
6. keep external providers available for high-quality reasoning and cross-checking.

The mobile UX must not change when the underlying PC becomes stronger.

## Invariants

- Stability > features.
- Reality > assumptions.
- Manual control > destructive automation.
- Context travels with code.
- Vercel discovers; Tailscale transports; DGM-MAT executes.
- Local LLM is optional capability, not a single point of failure.
