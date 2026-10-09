# DGM-MAT Architecture Decision: Headless Backend, Desktop Dashboard, Mobile Cockpit
<!-- Path: C:\ProgramasGodMode\DGM-MAT\docs\architecture\BACKEND_DESKTOP_MOBILE_BOUNDARIES.md -->

Date: 2026-10-09
Status: USER-CONFIRMED ARCHITECTURE DECISION

## Product surfaces

DGM-MAT has three distinct surfaces:

1. **PC backend/runtime — current priority.** Runs in the background without a visible terminal window or an open dashboard. It owns runtime state, governed execution, APIs, logs, approvals, and recovery.
2. **Desktop dashboard — later phase.** A comfortable desktop work surface for when the user is seated at the PC. It should be intuitive, practical, attractive but not over-designed, and conversational in a ChatGPT-like style. It is a client of the backend, not the backend itself.
3. **Mobile cockpit — later phase.** A separate responsive phone-first experience, sharing the same backend/API. It should synchronize with the PC automatically and must not require the user to type IP addresses manually.

## Current execution order

- Prioritize backend correctness, security, observability, stable API contracts, recovery, approval flow, and controlled integration tests.
- Do not divert current effort into visual redesign while backend work remains incomplete.
- After backend stability, build the desktop dashboard over stable APIs.
- Design and test safe PC/phone discovery and reconnection later, using the project's private-network approach (Tailscale is current context), authenticated device identity, and graceful offline behavior.

## Invariants

- Closing the dashboard must not stop the backend.
- The backend must not require a visible console window.
- Desktop and mobile clients must not run separate execution engines.
- Mobile connectivity must not expose the API publicly without authentication and an explicit network-security design.
- Never claim automatic sync is complete until discovery, authentication, reconnect, and offline scenarios have been tested.
- Stability > features; evidence > assumptions; manual control > destructive automation.

## Existing context

Previously recorded Tailscale addresses (PC 100.69.225.48, phone 100.109.173.115) are historical context only, not hardcoded requirements. The provider execution API remains governed and providers stay safe-off until explicit validation and activation gates are met. Preserve originals in DGM-MAT-OS before modifying existing source files. Never access or modify C:\ProgramasGodMode\DGM-MAT-FULL-MIRROR.
