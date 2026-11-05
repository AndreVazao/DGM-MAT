"use strict";

const API = "http://127.0.0.1:8181";
const CLIENT_ID = "dgm-mat-chrome-extension";
const RUN_KEY = "dgmRecoveryRun";
const TOKEN_KEY = "dgmRecoveryToken";
const TOKEN_EXPIRY_KEY = "dgmRecoveryTokenExpiresAt";

async function readState() {
  const data = await chrome.storage.local.get([TOKEN_KEY, TOKEN_EXPIRY_KEY, RUN_KEY]);
  const token = data[TOKEN_KEY] || "";
  const expiresAt = Number(data[TOKEN_EXPIRY_KEY] || 0);
  if (!token || Date.now() >= expiresAt) {
    await chrome.storage.local.remove([TOKEN_KEY, TOKEN_EXPIRY_KEY]);
    return { token: "", run: data[RUN_KEY] || null };
  }
  return { token, run: data[RUN_KEY] || null };
}

async function api(path, body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch(API + path, {
    method: "POST",
    headers,
    body: JSON.stringify(body || {})
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || ("DGM-MAT API returned HTTP " + response.status));
  return payload;
}

async function saveRun(run) {
  await chrome.storage.local.set({ [RUN_KEY]: run });
}

async function stopRun(reason) {
  const state = await readState();
  if (state.run) {
    state.run.active = false;
    state.run.last_error = reason || "";
    state.run.updated_at = new Date().toISOString();
    await saveRun(state.run);
  }
  await chrome.storage.local.set({ dgmRecoveryLastStatus: reason || "Stopped" });
}

async function sendToTab(tabId, message) {
  return chrome.tabs.sendMessage(tabId, message);
}

async function claimAndNavigate(run, token) {
  const result = await api("/recovery/browser-capture/next", {}, token);
  if (result.status !== "claimed" || !result.next) {
    run.active = false;
    run.current = null;
    run.updated_at = new Date().toISOString();
    await saveRun(run);
    await chrome.storage.local.set({ dgmRecoveryLastStatus: "Queue finished. All discovered conversations were processed." });
    return { finished: true };
  }
  run.current = result.next;
  run.updated_at = new Date().toISOString();
  await saveRun(run);
  const reply = await sendToTab(run.tab_id, { type: "DGM_NAVIGATE_TO", url: result.next.url });
  if (!reply || !reply.ok) throw new Error(reply?.error || "Could not navigate to the next conversation.");
  return { finished: false, next: result.next };
}

async function pair(code) {
  const result = await api("/auth/pair", { code, client_id: CLIENT_ID }, "");
  const expiry = Date.now() + Math.max(60, Number(result.expires_in || 1800) - 60) * 1000;
  await chrome.storage.local.set({
    [TOKEN_KEY]: result.access_token,
    [TOKEN_EXPIRY_KEY]: expiry,
    dgmRecoveryLastStatus: "Paired to local DGM-MAT."
  });
  return { expires_at: expiry, scopes: result.scopes || [] };
}

async function startRecovery(tabId) {
  const state = await readState();
  if (!state.token) throw new Error("Pair this extension with DGM-MAT first.");
  const reply = await sendToTab(tabId, { type: "DGM_DISCOVER_VISIBLE" });
  if (!reply || !reply.ok) throw new Error(reply?.error || "Could not read the visible conversation list.");
  const { provider, items } = reply.data;
  if (!Array.isArray(items) || !items.length) throw new Error("No accessible conversations were found on this provider page.");
  const discovered = await api("/recovery/browser-capture/discover", { provider, items }, state.token);
  const run = {
    active: true,
    provider,
    tab_id: tabId,
    discovered: discovered.registered,
    captured: 0,
    current: null,
    started_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    last_error: ""
  };
  await saveRun(run);
  await chrome.storage.local.set({ dgmRecoveryLastStatus: discovered.registered + " conversation(s) queued from " + provider + "." });
  return await claimAndNavigate(run, state.token);
}

async function handlePageReady(message, sender) {
  if (!sender.tab || !Number.isInteger(sender.tab.id)) return;
  const state = await readState();
  const run = state.run;
  if (!state.token || !run || !run.active || run.tab_id !== sender.tab.id) return;
  if (message.provider !== run.provider || !run.current || message.source_id !== run.current.source_id) return;

  try {
    const captured = await sendToTab(run.tab_id, { type: "DGM_CAPTURE_CURRENT" });
    if (!captured || !captured.ok) throw new Error(captured?.error || "Provider page capture failed.");
    const result = await api("/recovery/browser-capture/capture", captured.data, state.token);
    run.captured += 1;
    run.last_capture = {
      source_id: result.source_id,
      message_count: result.message_count,
      sha256: result.sha256,
      completeness: result.completeness
    };
    run.last_error = "";
    await saveRun(run);
    await chrome.storage.local.set({
      dgmRecoveryLastStatus: "Archived " + run.captured + "/" + run.discovered + ": " + result.source_id
    });
    await claimAndNavigate(run, state.token);
  } catch (error) {
    await stopRun(String(error.message || error));
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message.type !== "string") return false;
  if (message.type === "DGM_PAIR") {
    pair(String(message.code || "").trim())
      .then(result => sendResponse({ ok: true, data: result }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_START_RECOVERY") {
    startRecovery(Number(message.tabId))
      .then(result => sendResponse({ ok: true, data: result }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_STOP_RECOVERY") {
    stopRun("Stopped by operator.")
      .then(() => sendResponse({ ok: true }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_GET_STATUS") {
    readState()
      .then(state => chrome.storage.local.get("dgmRecoveryLastStatus").then(last => ({
        paired: Boolean(state.token),
        run: state.run,
        last_status: last.dgmRecoveryLastStatus || "Ready."
      })))
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_PROVIDER_PAGE_READY") {
    handlePageReady(message, sender).catch(error => stopRun(String(error.message || error)));
    sendResponse({ ok: true });
    return false;
  }
  return false;
});
