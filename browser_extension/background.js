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
    const run = data[RUN_KEY] || null;
    if (run?.active) {
      run.active = false;
      run.last_error = "local_session_expired";
      run.updated_at = new Date().toISOString();
      await saveRun(run);
    }
    return { token: "", run };
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
    if (state.run.current) {
      state.run.blocked = Array.isArray(state.run.blocked) ? state.run.blocked : [];
      if (!state.run.blocked.some(item => item.source_id === state.run.current.source_id)) {
        state.run.blocked.push(state.run.current);
      }
    }
    state.run.updated_at = new Date().toISOString();
    await saveRun(state.run);
  }
  await chrome.storage.local.set({ dgmRecoveryLastStatus: reason || "Stopped" });
}

async function sendToTab(tabId, message) {
  return chrome.tabs.sendMessage(tabId, message);
}

async function claimAndNavigate(run, token) {
  const result = await api("/recovery/browser-capture/next", { provider: run.provider }, token);
  if (result.status !== "claimed" || !result.next) {
    run.active = false;
    run.current = null;
    run.updated_at = new Date().toISOString();
    await saveRun(run);
    const blockedCount = Array.isArray(run.blocked) ? run.blocked.length : 0;
    await chrome.storage.local.set({
      dgmRecoveryLastStatus: blockedCount
        ? "Queue finished. " + blockedCount + " conversation(s) remain blocked for explicit retry." +
          (run.discovery_truncated ? " The provider list scan also hit its safety limit; scan again later." : "")
        : run.discovery_truncated
          ? "Queue finished for discovered items, but the list scan hit its safety limit. Scan again to find remaining conversations."
          : "Queue finished. All pending discovered conversations were archived."
    });
    return { finished: true, blocked: blockedCount };
  }
  run.current = result.next;
  run.updated_at = new Date().toISOString();
  await saveRun(run);
  try {
    const reply = await sendToTab(run.tab_id, { type: "DGM_NAVIGATE_TO", url: result.next.url });
    if (!reply || !reply.ok) throw new Error(reply?.error || "Could not navigate to the next conversation.");
  } catch (error) {
    await api("/recovery/browser-capture/block", {
      provider: run.provider,
      source_id: result.next.source_id,
      status: "failed",
      reason: "navigation_failed"
    }, token).catch(() => {});
    await stopRun(String(error.message || error));
    throw error;
  }
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
  const discovered = await api("/recovery/browser-capture/discover", { provider, items, truncated: Boolean(reply.data.truncated) }, state.token);
  const previousBlocked = Array.isArray(state.run?.blocked) ? [...state.run.blocked] : [];
  if (state.run?.current && !state.run.active &&
      !previousBlocked.some(item => item.source_id === state.run.current.source_id)) {
    previousBlocked.push(state.run.current);
  }
  const run = {
    active: true,
    provider,
    tab_id: tabId,
    discovered: discovered.pending,
    discovery_truncated: Boolean(discovered.discovery_truncated),
    captured: 0,
    blocked: previousBlocked,
    current: null,
    started_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    last_error: ""
  };
  await saveRun(run);
  await chrome.storage.local.set({ dgmRecoveryLastStatus: discovered.pending + " pending conversation(s) queued from " + provider + "." });
  return await claimAndNavigate(run, state.token);
}

async function retryCurrent(tabId) {
  const state = await readState();
  const run = state.run;
  if (!state.token || !run || run.active) {
    throw new Error("There is no available blocked conversation to retry.");
  }
  run.blocked = Array.isArray(run.blocked) ? run.blocked : [];
  const candidate = run.current || run.blocked[0];
  if (!candidate) throw new Error("There is no blocked conversation to retry.");
  if (!Number.isInteger(tabId)) throw new Error("Open the provider tab you want to retry first.");
  run.tab_id = tabId;
  run.provider = candidate.provider || run.provider;
  const query = "?provider=" + encodeURIComponent(candidate.provider || run.provider) +
    "&source_id=" + encodeURIComponent(candidate.source_id);
  await api("/recovery/browser-capture/retry" + query, {}, state.token);
  run.active = true;
  run.last_error = "";
  run.updated_at = new Date().toISOString();
  await saveRun(run);
  return await claimAndNavigate(run, state.token);
}

async function stopByOperator() {
  const state = await readState();
  if (state.token && state.run?.active && state.run.current) {
    await api("/recovery/browser-capture/block", {
      provider: state.run.provider,
      source_id: state.run.current.source_id,
      status: "blocked",
      reason: "operator_stopped"
    }, state.token).catch(() => {});
  }
  await stopRun("Stopped by operator.");
}

async function handlePageReady(message, sender) {
  if (!sender.tab || !Number.isInteger(sender.tab.id)) return;
  const state = await readState();
  const run = state.run;
  if (!state.token || !run || !run.active || run.tab_id !== sender.tab.id) return;
  if (message.blocked) {
    await api("/recovery/browser-capture/block", {
      provider: run.provider,
      source_id: run.current.source_id,
      status: message.blocked === "rate_limited" ? "rate_limited" : "blocked",
      reason: message.blocked
    }, state.token).catch(() => {});
    await stopRun(message.blocked);
    return;
  }
  if (message.provider !== run.provider || !run.current) return;
  if (message.source_id !== run.current.source_id) {
    await api("/recovery/browser-capture/block", {
      provider: run.provider,
      source_id: run.current.source_id,
      status: "failed",
      reason: "unexpected_conversation_identity"
    }, state.token).catch(() => {});
    await stopRun("Unexpected provider conversation identity; capture stopped.");
    return;
  }

  try {
    const captured = await sendToTab(run.tab_id, { type: "DGM_CAPTURE_CURRENT" });
    if (!captured || !captured.ok) throw new Error(captured?.error || "Provider page capture failed.");
    const result = await api("/recovery/browser-capture/capture", captured.data, state.token);
    run.captured += 1;
    run.blocked = (run.blocked || []).filter(item => item.source_id !== result.source_id);
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
    await api("/recovery/browser-capture/block", {
      provider: run.provider,
      source_id: run.current.source_id,
      status: "failed",
      reason: "capture_or_archive_failed"
    }, state.token).catch(() => {});
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
    stopByOperator()
      .then(() => sendResponse({ ok: true }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_RETRY_CURRENT") {
    retryCurrent(Number(message.tabId))
      .then(result => sendResponse({ ok: true, data: result }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_GET_STATUS") {
    readState()
      .then(state => chrome.storage.local.get("dgmRecoveryLastStatus").then(last => ({
        paired: Boolean(state.token),
        run: state.run,
        can_retry: Boolean(state.token && state.run && !state.run.active && (state.run.current || (state.run.blocked || []).length)),
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
