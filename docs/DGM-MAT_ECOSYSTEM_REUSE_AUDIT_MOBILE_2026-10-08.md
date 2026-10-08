# DGM-MAT Ecosystem Reuse Audit — Mobile/Cockpit — 2026-10-08

## Scope

Audited the current DGM-MAT cockpit architecture, DGM-MAT-Mobile, DGM-MAT-Deploy, DGM-Cockpit-Frontend and the legacy devops-god-mode project for reusable capability.

## Findings

### DGM-MAT

The current DGM-MAT runtime already provides:

- FastAPI runtime API;
- mobile WebSocket bridge;
- runtime truth/state;
- governance and approvals;
- conversation intelligence;
- provider registry;
- local AI fabric;
- federation/rendezvous;
- persistent storage;
- memory connectors.

The previous mobile bridge was only a transport stub. It did not provide a real conversation surface.

### DGM-MAT-Mobile

GitHub/local repository was effectively empty apart from README.

It is now the canonical mobile UI repository and contains a lightweight PWA.

### DGM-MAT-Deploy

The existing Vercel rendezvous service is healthy and production-ready.

Current Vercel project:

dgm-mat-rendezvous

Latest known deployment before this change was READY and connected to AndreVazao/DGM-MAT-Deploy main.

A public discovery path was added without exposing the rendezvous secret.

### DGM-Cockpit-Frontend

Local and GitHub repository are empty.

No implementation was imported.

### devops-god-mode

This repository contains extensive historical cockpit work and is a high-value reuse source.

Relevant capabilities found include:

- continuous operator conversation;
- rename/group behavior;
- mobile/offline synchronization;
- operator chat runtime;
- runtime snapshot;
- Ollama local brain;
- mobile pairing;
- provider conversation inventory.

These are evidence and source candidates, not DGM-MAT runtime dependencies.

## Architectural choice

Do not merge the whole legacy project into DGM-MAT.

Instead:

1. identify useful contracts;
2. reconstruct them under DGM-MAT ownership;
3. preserve provenance;
4. test independently;
5. retire or archive overlap only after the architecture is stable.

## Current implementation result

The first DGM-MAT-owned mobile conversation layer now supports:

- durable threads;
- rename;
- automatic initial title suggestion;
- deterministic intent understanding;
- local offline queue;
- reconnect replay;
- Vercel discovery;
- Tailscale target discovery;
- optional Ollama response path with a real low-memory guard.

## Reality check

The PC has only ~3 GB RAM and 2 logical CPUs.

Ollama models are installed, but a real qwen2.5:1.5b generation attempt failed because approximately 990.7 MiB was required while only approximately 831.7 MiB was available.

Therefore the current PC must not be treated as an always-on local-LLM server.

## Next

1. Enable Tailscale Serve once on the tailnet.
2. Publish DGM-MAT-Mobile through Vercel.
3. Register the HTTPS Tailscale endpoint in rendezvous.
4. Test mobile PWA from the phone.
5. Integrate conversation intent with the existing mission/orchestrator path.
6. Continue capability acquisition from the legacy cockpit sources only where evidence shows a missing DGM-MAT capability.
