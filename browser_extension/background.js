"use strict";

const API = "http://127.0.0.1:8181";
const CLIENT_ID = "dgm-mat-chrome-extension";
const RUN_KEY = "dgmRecoveryRun";
const TOKEN_KEY = "dgmRecoveryToken";
const TOKEN_EXPIRY_KEY = "dgmRecoveryTokenExpiresAt";
const AUTO_KEY = "dgmRecoveryAutoEnabled";
const PROVIDER_TABS_KEY = "dgmRecoveryProviderTabs";
const BROWSER_QUEUE_AUTO_KEY = "dgmBrowserOperatorAutoEnabled";
const BROWSER_TASK_KEY = "dgmBrowserOperatorCurrentTask";
const BROWSER_ALARM = "dgm-browser-operator-poll";
const PROVIDER_PAUSE_KEY = "dgmBrowserProviderPauses";
const CONSULT_ENABLED_KEY = "dgmBrowserConsultEnabled";
const CONSULT_CURRENT_KEY = "dgmBrowserConsultCurrent";
const CONSULT_ALARM = "dgm-browser-consult-poll";
let consultPollInProgress = false;
let browserPollInProgress = false;
let startInProgress = false;

async function pauseBrowserProvider(provider, reason) {
  if (!["chatgpt", "grok", "gemini", "deepseek", "qwen"].includes(provider)) return;
  const stored = await chrome.storage.local.get(PROVIDER_PAUSE_KEY);
  const pauses = stored[PROVIDER_PAUSE_KEY] || {};
  const cooldownMs = reason === "rate_limited" ? 60 * 60 * 1000 : 15 * 60 * 1000;
  pauses[provider] = {
    reason: String(reason || "provider_blocked"),
    paused_at: new Date().toISOString(),
    resume_after: Date.now() + cooldownMs
  };
  await chrome.storage.local.set({
    [PROVIDER_PAUSE_KEY]: pauses,
    dgmBrowserOperatorLastStatus: provider + " paused after " + pauses[provider].reason +
      "; another free provider will be tried and this one rechecked after cooldown."
  });
}

async function isBrowserProviderPaused(provider) {
  const stored = await chrome.storage.local.get(PROVIDER_PAUSE_KEY);
  const pauses = stored[PROVIDER_PAUSE_KEY] || {};
  const pause = pauses[provider];
  if (!pause) return false;
  if (Number(pause.resume_after) > Date.now()) return true;
  delete pauses[provider];
  await chrome.storage.local.set({ [PROVIDER_PAUSE_KEY]: pauses });
  return false;
}

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
  if (response.status === 401 && token) {
    await chrome.storage.local.remove([TOKEN_KEY, TOKEN_EXPIRY_KEY]);
    throw new Error("The local DGM-MAT session expired or the API restarted. Pair the extension again.");
  }
  if (!response.ok) throw new Error(payload.detail || ("DGM-MAT API returned HTTP " + response.status));
  return payload;
}

async function apiGet(path, token) {
  const response = await fetch(API + path, {
    method: "GET",
    headers: token ? { Authorization: "Bearer " + token } : {}
  });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401 && token) {
    await chrome.storage.local.remove([TOKEN_KEY, TOKEN_EXPIRY_KEY]);
    throw new Error("The local DGM-MAT session expired or the API restarted. Pair the extension again.");
  }
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

async function rememberProviderTab(provider, tabId) {
  if (!provider || !Number.isInteger(tabId)) return;
  const stored = await chrome.storage.local.get(PROVIDER_TABS_KEY);
  const tabs = stored[PROVIDER_TABS_KEY] || {};
  tabs[provider] = tabId;
  await chrome.storage.local.set({ [PROVIDER_TABS_KEY]: tabs });
}

async function startNextAutoProvider(excludeProvider) {
  const state = await readState();
  if (!state.token || state.run?.active) return { started: false };
  const stored = await chrome.storage.local.get([AUTO_KEY, PROVIDER_TABS_KEY]);
  if (!stored[AUTO_KEY]) return { started: false };
  const tabs = stored[PROVIDER_TABS_KEY] || {};
  for (const provider of ["chatgpt", "grok", "gemini", "deepseek", "qwen"]) {
    if (provider === excludeProvider || !Number.isInteger(tabs[provider])) continue;
    if (await isBrowserProviderPaused(provider)) continue;
    try {
      const result = await startRecovery(tabs[provider], false);
      if (!result.finished) return { started: true, provider };
    } catch (error) {
      await chrome.storage.local.set({
        dgmRecoveryLastStatus: "Automatic start for " + provider + " stopped: " + String(error.message || error)
      });
    }
  }
  return { started: false };
}

async function setAutoRecovery(enabled, tabId) {
  await chrome.storage.local.set({ [AUTO_KEY]: Boolean(enabled) });
  if (!enabled) {
    await chrome.storage.local.set({
      dgmRecoveryLastStatus: "Automatic recovery disabled. Any active queue continues until stopped or finished."
    });
    return { enabled: false };
  }
  if (Number.isInteger(tabId)) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.id === tabId) {
      const result = await startRecovery(tabId);
      return { enabled: true, started: !result.finished };
    }
  }
  return { enabled: true, started: false };
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

async function listBrowserConsultations() {
  const state = await readState();
  if (!state.token) throw new Error("Pair the extension with DGM-MAT first.");
  return apiGet("/recovery/browser-consult/status", state.token);
}

async function loadMissionConsultationContext(payload) {
  const state = await readState();
  if (!state.token) throw new Error("Pair the extension with DGM-MAT first.");
  return api("/recovery/browser-consult/mission-context", payload, state.token);
}

async function previewBrowserConsultation(payload) {
  const state = await readState();
  if (!state.token) throw new Error("Pair the extension with DGM-MAT first.");
  return api("/recovery/browser-consult/preview", payload, state.token);
}

async function enqueueBrowserConsultation(payload) {
  const state = await readState();
  if (!state.token) throw new Error("Pair the extension with DGM-MAT first.");
  return api("/recovery/browser-consult/enqueue", payload, state.token);
}

async function approveBrowserConsultation(consultationId) {
  const state = await readState();
  if (!state.token) throw new Error("Pair the extension with DGM-MAT first.");
  const result = await api("/recovery/browser-consult/approve/" + encodeURIComponent(consultationId), {}, state.token);
  await pollBrowserConsultQueue().catch(() => {});
  return result;
}

async function setAutoBrowserConsult(enabled) {
  const state = await readState();
  if (enabled && !state.token) throw new Error("Pair the extension with DGM-MAT before enabling AI consultation.");
  await chrome.storage.local.set({ [CONSULT_ENABLED_KEY]: Boolean(enabled) });
  if (enabled) {
    chrome.alarms.create(CONSULT_ALARM, { periodInMinutes: 1 });
    await pollBrowserConsultQueue();
  } else {
    await chrome.alarms.clear(CONSULT_ALARM);
  }
  return { enabled: Boolean(enabled) };
}

async function pollBrowserConsultQueue() {
  if (consultPollInProgress) return;
  consultPollInProgress = true;
  try {
    const settings = await chrome.storage.local.get([CONSULT_ENABLED_KEY, PROVIDER_TABS_KEY, CONSULT_CURRENT_KEY, BROWSER_TASK_KEY]);
    if (browserPollInProgress) return;
    const state = await readState();
    if (!state.token) return;
    if (settings[CONSULT_CURRENT_KEY]) {
      const interrupted = settings[CONSULT_CURRENT_KEY];
      await api("/recovery/browser-consult/block", {
        consultation_id: interrupted.consultation_id,
        claim_token: interrupted.claim_token,
        reason: "interrupted"
      }, state.token).catch(() => {});
      await chrome.storage.local.remove(CONSULT_CURRENT_KEY);
      await chrome.storage.local.set({
        dgmBrowserConsultLastStatus: "Previous consultation was interrupted by extension restart; it was not replayed."
      });
      return;
    }
    if (settings[BROWSER_TASK_KEY] || !settings[CONSULT_ENABLED_KEY] || state.run?.active) return;
    const tabs = settings[PROVIDER_TABS_KEY] || {};
    for (const provider of ["chatgpt", "grok", "gemini", "deepseek", "qwen"]) {
      if (await isBrowserProviderPaused(provider)) continue;
      const tabId = tabs[provider];
      if (!Number.isInteger(tabId)) continue;
      let tab;
      try { tab = await chrome.tabs.get(tabId); } catch (_) { continue; }
      if (!tab) continue;
      const peek = await apiGet(
        "/recovery/browser-consult/peek?provider=" + encodeURIComponent(provider),
        state.token
      );
      if (peek.status !== "pending" || !peek.next) continue;
      let readiness;
      try {
        readiness = await sendToTab(
          tabId,
          { type: peek.next.review_mode === "fresh_review" ? "DGM_FRESH_REVIEW_PING" : "DGM_PROVIDER_PING" }
        );
      } catch (_) { continue; }
      const freshMode = peek.next.review_mode === "fresh_review";
      const ready = freshMode
        ? Boolean(
            readiness?.ok &&
            readiness.fresh_review_ready === true &&
            readiness.provider === provider &&
            readiness.preflight_nonce &&
            readiness.privacy_mode_verified === true
          )
        : Boolean(
            readiness?.ok &&
            readiness.provider === provider &&
            readiness.source_id &&
            !readiness.blocked
          );
      if (!ready) {
        await chrome.storage.local.set({
          dgmBrowserConsultLastStatus: provider + " waiting for " +
            (freshMode ? "a verified temporary privacy-mode blank page." : "an existing conversation tab.")
        });
        continue;
      }
      const claimed = await api("/recovery/browser-consult/next?provider=" + encodeURIComponent(provider), {}, state.token);
      if (claimed.status !== "claimed" || !claimed.next) continue;
      const task = { ...claimed.next, tab_id: tabId };
      if (task.review_mode !== peek.next.review_mode ||
          task.consultation_id !== peek.next.consultation_id) {
        await api("/recovery/browser-consult/block", {
          consultation_id: task.consultation_id,
          claim_token: task.claim_token,
          reason: "ui_mismatch"
        }, state.token).catch(() => {});
        return;
      }
      task.source_id = freshMode ? null : readiness.source_id;
      // Persist before touching the provider UI. A worker restart never replays this one-shot claim.
      await chrome.storage.local.set({ [CONSULT_CURRENT_KEY]: task });
      try {
        const response = task.review_mode === "fresh_review"
          ? await sendToTab(tabId, {
              type: "DGM_EXECUTE_FRESH_REVIEW",
              provider,
              preflight_nonce: readiness.preflight_nonce,
              message: task.prompt,
              response_timeout_ms: 180000
            })
          : await sendToTab(tabId, {
              type: "DGM_EXECUTE_BROWSER_TASK",
              provider,
              source_id: task.source_id,
              message: task.prompt,
              response_timeout_ms: 180000
            });
        if (!response?.ok) throw new Error(response?.error || "Provider UI consultation failed.");
        const outcome = response.data || {};
        if (outcome.status === "completed" && typeof outcome.assistant_text === "string" && outcome.assistant_text.trim()) {
          const resultPayload = {
            consultation_id: task.consultation_id,
            claim_token: task.claim_token,
            response_text: outcome.assistant_text.slice(0, 16000)
          };
          if (task.review_mode === "fresh_review") {
            resultPayload.evidence = {
              provider,
              source_id: outcome.source_id,
              initial_source_id: outcome.initial_source_id,
              initial_visible_message_count: outcome.initial_visible_message_count,
              privacy_mode: outcome.privacy_mode,
              privacy_mode_verified: outcome.privacy_mode_verified,
              verification: outcome.verification
            };
          }
          await api("/recovery/browser-consult/result", resultPayload, state.token);
          await chrome.storage.local.set({ dgmBrowserConsultLastStatus: provider + " consultation completed; answer stored as untrusted." });
        } else {
          const reason = outcome.reason === "rate_limited" ? "rate_limited"
            : outcome.reason === "blocked_login" ? "blocked_login"
            : outcome.reason === "blocked_challenge" ? "blocked_challenge"
            : "interrupted";
          await api("/recovery/browser-consult/block", {
            consultation_id: task.consultation_id,
            claim_token: task.claim_token,
            reason
          }, state.token);
          if (reason !== "interrupted") await pauseBrowserProvider(provider, reason);
          await chrome.storage.local.set({ dgmBrowserConsultLastStatus: provider + " consultation stopped: " + reason + "; no automatic retry." });
        }
      } catch (error) {
        await api("/recovery/browser-consult/block", {
          consultation_id: task.consultation_id,
          claim_token: task.claim_token,
          reason: "interrupted"
        }, state.token).catch(() => {});
        await chrome.storage.local.set({
          dgmBrowserConsultLastStatus: provider + " consultation interrupted; it will not be replayed automatically."
        });
      } finally {
        await chrome.storage.local.remove(CONSULT_CURRENT_KEY);
      }
      return;
    }
  } catch (error) {
    await chrome.storage.local.set({
      dgmBrowserConsultLastStatus: "AI consultation paused: " + String(error.message || error)
    });
  } finally {
    consultPollInProgress = false;
  }
}

async function setAutoBrowserOperator(enabled) {
  const state = await readState();
  if (enabled && !state.token) throw new Error("Pair the extension with DGM-MAT before enabling mission execution.");
  await chrome.storage.local.set({ [BROWSER_QUEUE_AUTO_KEY]: Boolean(enabled) });
  if (enabled) {
    chrome.alarms.create(BROWSER_ALARM, { periodInMinutes: 0.5 });
    await pollBrowserOperatorQueue();
  } else {
    await chrome.alarms.clear(BROWSER_ALARM);
  }
  return { enabled: Boolean(enabled) };
}

async function finishBrowserOperatorTask(task, token, outcome) {
  if (outcome?.status === "blocked") {
    await pauseBrowserProvider(task.provider, outcome.reason);
    await api("/browser-operator/tasks/" + encodeURIComponent(task.task_id) + "/fail", {
      claim_token: task.claim_token,
      reason: String(outcome.reason || "provider_blocked"),
      blocked: true
    }, token);
  } else {
    const status = outcome?.status === "completed" ? "completed" : "unverified";
    await api("/browser-operator/tasks/" + encodeURIComponent(task.task_id) + "/result", {
      claim_token: task.claim_token,
      status,
      result: outcome || { status: "unverified", reason: "empty_browser_result" }
    }, token);
  }
  await chrome.storage.local.remove(BROWSER_TASK_KEY);
  await chrome.storage.local.set({
    dgmBrowserOperatorLastStatus: outcome?.status === "completed"
      ? "Mission task completed: " + task.task_id
      : outcome?.status === "blocked"
        ? "Mission task blocked: " + String(outcome.reason || "provider_blocked")
        : "Mission task sent but not fully verified: " + task.task_id
  });
}

async function executePendingBrowserOperatorTask(task, tabId, token) {
  try {
    const response = await sendToTab(tabId, {
      type: "DGM_EXECUTE_BROWSER_TASK",
      provider: task.provider,
      source_id: task.source_id,
      message: task.message,
      response_timeout_ms: 120000
    });
    if (!response?.ok) throw new Error(response?.error || "Browser task execution failed.");
    await finishBrowserOperatorTask(task, token, response.data);
  } catch (error) {
    await api("/browser-operator/tasks/" + encodeURIComponent(task.task_id) + "/fail", {
      claim_token: task.claim_token,
      reason: String(error.message || error),
      blocked: false
    }, token).catch(() => {});
    await chrome.storage.local.remove(BROWSER_TASK_KEY);
    await chrome.storage.local.set({
      dgmBrowserOperatorLastStatus: "Mission task failed and will not be replayed automatically: " + task.task_id
    });
  }
}

async function pollBrowserOperatorQueue() {
  if (browserPollInProgress || consultPollInProgress) return;
  browserPollInProgress = true;
  try {
    const settings = await chrome.storage.local.get([BROWSER_QUEUE_AUTO_KEY, PROVIDER_TABS_KEY, BROWSER_TASK_KEY, CONSULT_CURRENT_KEY]);
    if (!settings[BROWSER_QUEUE_AUTO_KEY] || settings[BROWSER_TASK_KEY] || settings[CONSULT_CURRENT_KEY]) return;
    const state = await readState();
    if (!state.token || state.run?.active) return;
    const tabs = settings[PROVIDER_TABS_KEY] || {};
    for (const provider of ["chatgpt", "grok", "gemini", "deepseek", "qwen"]) {
      if (await isBrowserProviderPaused(provider)) continue;
      const tabId = tabs[provider];
      if (!Number.isInteger(tabId)) continue;
      let tab;
      try { tab = await chrome.tabs.get(tabId); } catch (_) { continue; }
      if (!tab) continue;
      let readiness;
      try {
        readiness = await sendToTab(tabId, { type: "DGM_PROVIDER_PING" });
      } catch (_) {
        // Never claim a durable task until the content script confirms it is ready.
        continue;
      }
      if (!readiness?.ok || readiness.provider !== provider) continue;
      if (readiness.blocked) {
        await pauseBrowserProvider(provider, readiness.blocked);
        continue;
      }
      const response = await apiGet("/browser-operator/next?provider=" + encodeURIComponent(provider), state.token);
      if (response.status !== "claimed" || !response.task) continue;
      const task = { ...response.task, tab_id: tabId };
      await chrome.storage.local.set({ [BROWSER_TASK_KEY]: task });
      try {
        if (tab.url !== task.conversation_url) {
          await chrome.tabs.update(tabId, { url: task.conversation_url });
        } else {
          await executePendingBrowserOperatorTask(task, tabId, state.token);
        }
      } catch (error) {
        await api("/browser-operator/tasks/" + encodeURIComponent(task.task_id) + "/fail", {
          claim_token: task.claim_token,
          reason: String(error.message || error),
          blocked: false
        }, state.token).catch(() => {});
        await chrome.storage.local.remove(BROWSER_TASK_KEY);
      }
      return;
    }
  } catch (error) {
    await chrome.storage.local.set({
      dgmBrowserOperatorLastStatus: "Browser mission queue paused: " + String(error.message || error)
    });
  } finally {
    browserPollInProgress = false;
  }
}

function providerForTabUrl(value) {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    if (host === "chatgpt.com" || host === "chat.openai.com") return "chatgpt";
    if (host === "gemini.google.com" || host === "bard.google.com") return "gemini";
    if (host === "grok.com" || (host === "x.com" && url.pathname.startsWith("/i/grok"))) return "grok";
    if (host === "chat.deepseek.com") return "deepseek";
    if (host === "chat.qwen.ai") return "qwen";
  } catch (_) {}
  return null;
}

async function pair(code) {
  const result = await api("/auth/pair", { code, client_id: CLIENT_ID }, "");
  const expiry = Date.now() + Math.max(60, Number(result.expires_in || 1800) - 60) * 1000;
  await chrome.storage.local.set({
    [TOKEN_KEY]: result.access_token,
    [TOKEN_EXPIRY_KEY]: expiry
  });
  const current = await chrome.storage.local.get([AUTO_KEY, BROWSER_QUEUE_AUTO_KEY, CONSULT_ENABLED_KEY]);
  const defaults = {};
  if (typeof current[AUTO_KEY] !== "boolean") defaults[AUTO_KEY] = true;
  if (typeof current[BROWSER_QUEUE_AUTO_KEY] !== "boolean") defaults[BROWSER_QUEUE_AUTO_KEY] = true;
  if (typeof current[CONSULT_ENABLED_KEY] !== "boolean") defaults[CONSULT_ENABLED_KEY] = false;
  if (Object.keys(defaults).length) await chrome.storage.local.set(defaults);
  const settings = await chrome.storage.local.get([AUTO_KEY, BROWSER_QUEUE_AUTO_KEY, CONSULT_ENABLED_KEY]);
  const tabs = await chrome.tabs.query({});
  const providerTabs = {};
  for (const tab of tabs) {
    if (!Number.isInteger(tab.id)) continue;
    const provider = providerForTabUrl(tab.url || "");
    if (!provider) continue;
    providerTabs[provider] = tab.id;
    await rememberProviderTab(provider, tab.id);
  }
  await chrome.storage.local.set({
    dgmRecoveryLastStatus: "Paired to local DGM-MAT; automatic recovery and approved mission queue are enabled by default."
  });
  if (settings[BROWSER_QUEUE_AUTO_KEY]) {
    chrome.alarms.create(BROWSER_ALARM, { periodInMinutes: 0.5 });
    await pollBrowserOperatorQueue().catch(() => {});
  }
  if (settings[CONSULT_ENABLED_KEY]) {
    chrome.alarms.create(CONSULT_ALARM, { periodInMinutes: 1 });
    await pollBrowserConsultQueue().catch(() => {});
  }
  if (settings[AUTO_KEY]) {
    for (const provider of ["chatgpt", "grok", "gemini", "deepseek", "qwen"]) {
      const tabId = providerTabs[provider];
      if (!Number.isInteger(tabId) || await isBrowserProviderPaused(provider)) continue;
      try {
        const started = await startRecovery(tabId);
        if (!started.finished) break;
      } catch (error) {
        await chrome.storage.local.set({
          dgmRecoveryLastStatus: "Paired; automatic recovery will retry when a provider tab is ready: " +
            String(error.message || error)
        });
      }
    }
  }
  return {
    expires_at: expiry,
    scopes: result.scopes || [],
    auto_recovery_enabled: Boolean(settings[AUTO_KEY]),
    browser_operator_auto_enabled: Boolean(settings[BROWSER_QUEUE_AUTO_KEY]),
    provider_tabs_found: Object.keys(providerTabs).length
  };
}

async function startRecovery(tabId, chainOnEmpty = true) {
  if (startInProgress) throw new Error("A provider recovery start is already being prepared.");
  startInProgress = true;
  try {
  const state = await readState();
  if (!state.token) throw new Error("Pair this extension with DGM-MAT first.");
  if (state.run?.active) {
    return { finished: false, already_active: true, next: state.run.current };
  }
  const reply = await sendToTab(tabId, { type: "DGM_DISCOVER_VISIBLE" });
  if (!reply || !reply.ok) throw new Error(reply?.error || "Could not read the visible conversation list.");
  const { provider, items } = reply.data;
  if (!Array.isArray(items) || !items.length) throw new Error("No accessible conversations were found on this provider page.");
  const settings = await chrome.storage.local.get(AUTO_KEY);
  const previous = state.run;
  if (settings[AUTO_KEY] && previous?.current && !previous.active &&
      previous.current.provider === provider &&
      (previous.last_error === "provider_tab_closed" ||
       /session expired|API restarted/i.test(previous.last_error || ""))) {
    const retryQuery = "?provider=" + encodeURIComponent(provider) +
      "&source_id=" + encodeURIComponent(previous.current.source_id);
    await api("/recovery/browser-capture/retry" + retryQuery, {}, state.token);
  }
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
  const result = await claimAndNavigate(run, state.token);
  startInProgress = false;
  if (result.finished && chainOnEmpty) await startNextAutoProvider(provider);
  return result;
  } finally {
    startInProgress = false;
  }
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
  await rememberProviderTab(message.provider, sender.tab.id);
  const state = await readState();
  const run = state.run;
  if (!state.token) return;
  const pendingState = await chrome.storage.local.get(BROWSER_TASK_KEY);
  const pendingTask = pendingState[BROWSER_TASK_KEY];
  if (pendingTask && pendingTask.tab_id === sender.tab.id) {
    if (message.blocked) {
      await pauseBrowserProvider(pendingTask.provider, message.blocked);
      await api("/browser-operator/tasks/" + encodeURIComponent(pendingTask.task_id) + "/fail", {
        claim_token: pendingTask.claim_token,
        reason: message.blocked,
        blocked: true
      }, state.token).catch(() => {});
      await chrome.storage.local.remove(BROWSER_TASK_KEY);
      await chrome.storage.local.set({ dgmBrowserOperatorLastStatus: "Mission task blocked: " + message.blocked });
      await pollBrowserOperatorQueue().catch(() => {});
      return;
    }
    if (message.provider !== pendingTask.provider) return;
    if (message.source_id !== pendingTask.source_id) {
      try { await chrome.tabs.update(sender.tab.id, { url: pendingTask.conversation_url }); }
      catch (error) {
        await api("/browser-operator/tasks/" + encodeURIComponent(pendingTask.task_id) + "/fail", {
          claim_token: pendingTask.claim_token,
          reason: String(error.message || error),
          blocked: false
        }, state.token).catch(() => {});
        await chrome.storage.local.remove(BROWSER_TASK_KEY);
      }
      return;
    }
    await executePendingBrowserOperatorTask(pendingTask, sender.tab.id, state.token);
    return;
  }
  if (!run || !run.active) {
    const settings = await chrome.storage.local.get(AUTO_KEY);
    if (settings[AUTO_KEY] && message.provider) {
      try { await startRecovery(sender.tab.id); }
      catch (error) {
        await chrome.storage.local.set({
          dgmRecoveryLastStatus: "Automatic recovery could not start: " + String(error.message || error)
        });
      }
    }
    return;
  }
  if (run.tab_id !== sender.tab.id) return;
  if (message.blocked) {
    await pauseBrowserProvider(run.provider, message.blocked);
    await api("/recovery/browser-capture/block", {
      provider: run.provider,
      source_id: run.current.source_id,
      status: message.blocked === "rate_limited" ? "rate_limited" : "blocked",
      reason: message.blocked
    }, state.token).catch(() => {});
    await stopRun(message.blocked);
    await startNextAutoProvider(run.provider);
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
    await startNextAutoProvider(run.provider);
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
    const next = await claimAndNavigate(run, state.token);
    if (next.finished) await startNextAutoProvider(run.provider);
  } catch (error) {
    await api("/recovery/browser-capture/block", {
      provider: run.provider,
      source_id: run.current.source_id,
      status: "failed",
      reason: "capture_or_archive_failed"
    }, state.token).catch(() => {});
    await stopRun(String(error.message || error));
    await startNextAutoProvider(run.provider);
  }
}

async function handleProviderTabRemoved(tabId) {
  const state = await readState();
  const stored = await chrome.storage.local.get(PROVIDER_TABS_KEY);
  const tabs = stored[PROVIDER_TABS_KEY] || {};
  let changed = false;
  for (const [provider, knownTabId] of Object.entries(tabs)) {
    if (knownTabId === tabId) {
      delete tabs[provider];
      changed = true;
    }
  }
  if (changed) await chrome.storage.local.set({ [PROVIDER_TABS_KEY]: tabs });

  if (state.run?.active && state.run.tab_id === tabId) {
    if (state.token && state.run.current) {
      await api("/recovery/browser-capture/block", {
        provider: state.run.provider,
        source_id: state.run.current.source_id,
        status: "failed",
        reason: "provider_tab_closed"
      }, state.token).catch(() => {});
    }
    const interruptedProvider = state.run.provider;
    await stopRun("provider_tab_closed");
    await startNextAutoProvider(interruptedProvider);
  }
}

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm?.name === BROWSER_ALARM) pollBrowserOperatorQueue().catch(() => {});
  if (alarm?.name === CONSULT_ALARM) pollBrowserConsultQueue().catch(() => {});
});
chrome.runtime.onStartup.addListener(() => {
  chrome.storage.local.get([BROWSER_QUEUE_AUTO_KEY, CONSULT_ENABLED_KEY]).then(settings => {
    if (settings[BROWSER_QUEUE_AUTO_KEY]) {
      chrome.alarms.create(BROWSER_ALARM, { periodInMinutes: 0.5 });
      pollBrowserOperatorQueue().catch(() => {});
    }
    if (settings[CONSULT_ENABLED_KEY]) {
      chrome.alarms.create(CONSULT_ALARM, { periodInMinutes: 1 });
      pollBrowserConsultQueue().catch(() => {});
    }
  });
});
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get([BROWSER_QUEUE_AUTO_KEY, CONSULT_ENABLED_KEY]).then(settings => {
    if (settings[BROWSER_QUEUE_AUTO_KEY]) chrome.alarms.create(BROWSER_ALARM, { periodInMinutes: 0.5 });
    if (settings[CONSULT_ENABLED_KEY]) chrome.alarms.create(CONSULT_ALARM, { periodInMinutes: 1 });
  });
});

chrome.tabs.onRemoved.addListener(tabId => {
  handleProviderTabRemoved(tabId).catch(() => {});
});


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
  if (message.type === "DGM_LIST_BROWSER_CONSULTS") {
    listBrowserConsultations()
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_LOAD_MISSION_CONSULT_CONTEXT") {
    loadMissionConsultationContext(message.payload || {})
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_PREVIEW_BROWSER_CONSULT") {
    previewBrowserConsultation(message.payload || {})
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_ENQUEUE_BROWSER_CONSULT") {
    enqueueBrowserConsultation(message.payload || {})
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_APPROVE_BROWSER_CONSULT") {
    approveBrowserConsultation(String(message.consultationId || ""))
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_SET_AUTO_BROWSER_CONSULT") {
    setAutoBrowserConsult(Boolean(message.enabled))
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_SET_AUTO_BROWSER_OPERATOR") {
    setAutoBrowserOperator(Boolean(message.enabled))
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_SET_AUTO_RECOVERY") {
    setAutoRecovery(Boolean(message.enabled), Number.isInteger(message.tabId) ? message.tabId : null)
      .then(data => sendResponse({ ok: true, data }))
      .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message.type === "DGM_GET_STATUS") {
    readState()
      .then(async state => {
        const [last, settings] = await Promise.all([
          chrome.storage.local.get("dgmRecoveryLastStatus"),
          chrome.storage.local.get([AUTO_KEY, BROWSER_QUEUE_AUTO_KEY, CONSULT_ENABLED_KEY, "dgmBrowserOperatorLastStatus", "dgmBrowserConsultLastStatus"])
        ]);
        return {
          paired: Boolean(state.token),
          run: state.run,
          auto_enabled: Boolean(settings[AUTO_KEY]),
          browser_operator_auto_enabled: Boolean(settings[BROWSER_QUEUE_AUTO_KEY]),
          browser_consult_enabled: Boolean(settings[CONSULT_ENABLED_KEY]),
          browser_consult_status: settings.dgmBrowserConsultLastStatus || "AI consultation idle.",
          browser_operator_status: settings.dgmBrowserOperatorLastStatus || "Browser mission operator idle.",
          can_retry: Boolean(state.token && state.run && !state.run.active && (state.run.current || (state.run.blocked || []).length)),
          last_status: last.dgmRecoveryLastStatus || "Ready."
        };
      })
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
