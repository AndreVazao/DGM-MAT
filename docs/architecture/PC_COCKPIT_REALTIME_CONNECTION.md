# DGM-MAT PC Cockpit — real-time connection and UI-thread safety

Date: 2026-10-10
Status: **LOCAL DESKTOP CONNECTION FIX IMPLEMENTED; LOOPBACK API/WEBSOCKET HANDSHAKE VERIFIED; FULL Qt-to-runtime E2E STILL TO VERIFY**

## Findings

- The existing PC cockpit is a PySide6 desktop application in `cockpit/main_window.py`, launched through `cockpit.app.run_cockpit`.
- The previous connection bootstrap called `asyncio.get_running_loop()` from the Qt GUI thread and silently did nothing when no event loop existed. This left the realtime client disconnected in normal desktop launch.
- Realtime messages and the initial HTTP hydration could call Qt widget methods from non-GUI threads, which is unsafe.

## Changes

- `MainWindow` now starts its async WebSocket client on a dedicated daemon thread with `asyncio.run()`.
- Realtime messages and connection state cross to the Qt GUI thread using `Signal`/`Slot`; initial state hydration emits the same signal instead of mutating widgets from its worker thread.
- Closing the desktop window asks the realtime client to stop and close its WebSocket. Core is not stopped by closing the cockpit.
- A stop-before-connect guard prevents a quick window close from racing with a later connection start.
- Tests cover Qt-signal dispatch and stop-before-connect behavior.

## Security boundary

- API default host remains `127.0.0.1`; no remote bind, public port, Vercel relay or mobile endpoint was added.
- The current API has legacy routes without global auth and permissive CORS; do not bind it to a LAN/Tailscale interface or expose it remotely. A local desktop cockpit connection is not proof that global auth is complete.
- Do not add intervention mutation endpoints until global HTTP/WebSocket auth, operator/device identity, scopes, revocation, replay protection and audit are enforced.

## Validation

Run `python -m pytest tests/cockpit -q`, compile the two modified modules, and run `git diff --check`. The cockpit suite passed **7 tests**. Live checks against the already-running local Core returned `/health` HTTP 200, `/runtime/truth` HTTP 200, and a successful WebSocket handshake at `ws://127.0.0.1:8181/ws`. This verifies the local endpoint/handshake, but not yet a full visual Qt session receiving a real state event end-to-end.

## Next PC cockpit tasks

1. Validate live local API/WebSocket connectivity without changing Core lifecycle.
2. Build a dedicated intervention view backed by an authenticated local API contract; display WAITING_FOR_USER and expiry without leaking secrets.
3. Make chat/mission submission non-blocking in the UI thread.
4. Only after local cockpit and API auth are verified, design paired multi-device clients and then Android APK.
