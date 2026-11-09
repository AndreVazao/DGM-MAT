(() => {
  "use strict";

  const VERSION = "0.1.3";
  const PROVIDER_HOSTS = {
    chatgpt: new Set(["chatgpt.com", "chat.openai.com"]),
    gemini: new Set(["gemini.google.com", "bard.google.com"]),
    grok: new Set(["grok.com", "x.com"]),
    deepseek: new Set(["chat.deepseek.com"]),
    qwen: new Set(["chat.qwen.ai"])
  };

  function providerForUrl(value) {
    try {
      const url = new URL(value);
      const host = url.hostname.toLowerCase();
      if (PROVIDER_HOSTS.chatgpt.has(host)) return "chatgpt";
      if (PROVIDER_HOSTS.gemini.has(host)) return "gemini";
      if (PROVIDER_HOSTS.grok.has(host)) {
        if (host === "x.com" && !url.pathname.startsWith("/i/grok")) return null;
        return "grok";
      }
      if (PROVIDER_HOSTS.deepseek.has(host)) return "deepseek";
      if (PROVIDER_HOSTS.qwen.has(host)) return "qwen";
    } catch (_) {}
    return null;
  }

  function sourceIdForUrl(value, provider) {
    const url = new URL(value);
    const segments = url.pathname.split("/").filter(Boolean);
    if (provider === "chatgpt") {
      const index = segments.indexOf("c");
      return index >= 0 ? segments[index + 1] || null : null;
    }
    if (provider === "gemini") {
      const index = segments.indexOf("app");
      return index >= 0 ? segments[index + 1] || null : null;
    }
    const queryKeys = provider === "deepseek" || provider === "qwen"
      ? ["conversation", "conversationId", "chatId", "chat_id", "id"]
      : ["conversation", "id"];
    for (const key of queryKeys) {
      const queryId = url.searchParams.get(key);
      if (queryId && /^[A-Za-z0-9._:-]{1,200}$/.test(queryId)) return queryId;
    }
    if (provider === "deepseek") {
      const index = segments.indexOf("chat");
      if (index >= 0) {
        const candidate = segments[index + 1] === "s" ? segments[index + 2] : segments[index + 1];
        return candidate && /^[A-Za-z0-9_-]+$/.test(candidate) ? candidate : null;
      }
      return null;
    }
    if (provider === "qwen") {
      for (const marker of ["chat", "c", "conversation", "s"]) {
        const index = segments.indexOf(marker);
        if (index >= 0 && segments[index + 1] && /^[A-Za-z0-9_-]+$/.test(segments[index + 1])) {
          return segments[index + 1];
        }
      }
      return null;
    }
    for (const marker of ["chat", "c"]) {
      const index = segments.indexOf(marker);
      if (index >= 0 && segments[index + 1] && /^[A-Za-z0-9_-]+$/.test(segments[index + 1])) {
        return segments[index + 1];
      }
    }
    const grokIndex = segments.indexOf("i");
    return grokIndex >= 0 && segments[grokIndex + 1] === "grok" ? segments[grokIndex + 2] || null : null;
  }

  function conversationTitle(anchor, url) {
    const text = (anchor?.innerText || anchor?.getAttribute("aria-label") || "").trim();
    if (text) return text.slice(0, 500);
    const title = (document.title || "").replace(/\s*[|—-]\s*(ChatGPT|Gemini|Grok|DeepSeek|Qwen).*$/i, "").trim();
    return title.slice(0, 500) || "Conversation " + url.pathname.split("/").filter(Boolean).pop();
  }

  function isConversationUrl(value, provider) {
    const id = sourceIdForUrl(value, provider);
    if (!id) return false;
    const url = new URL(value);
    if (provider === "grok" && url.hostname === "x.com" && !url.pathname.startsWith("/i/grok")) return false;
    return true;
  }

  async function discoverConversations() {
    const provider = providerForUrl(location.href);
    if (!provider) throw new Error("This tab is not an allowed AI provider page.");
    const found = new Map();
    let truncated = false;

    function collectLinks() {
      if (isConversationUrl(location.href, provider)) {
        const id = sourceIdForUrl(location.href, provider);
        if (id && !found.has(id)) {
          found.set(id, {
            source_id: id,
            title: conversationTitle(null, location.href),
            url: location.href,
            source_date: "unknown-date"
          });
        }
      }
      for (const anchor of document.querySelectorAll("a[href]")) {
        let url;
        try { url = new URL(anchor.href, location.href); } catch (_) { continue; }
        if (url.origin !== location.origin || !isConversationUrl(url.href, provider)) continue;
        const id = sourceIdForUrl(url.href, provider);
        if (!id || found.has(id)) continue;
        found.set(id, {
          source_id: id,
          title: conversationTitle(anchor, url),
          url: url.href,
          source_date: "unknown-date"
        });
        if (found.size >= 500) break;
      }
    }

    collectLinks();
    const navs = [...document.querySelectorAll("nav, [role='navigation']")];
    for (const nav of navs) {
      const scrollers = [...nav.querySelectorAll("*")]
        .filter(element => element.scrollHeight > element.clientHeight + 100)
        .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))
        .slice(0, 2);
      for (const scroller of scrollers) {
        const originalTop = scroller.scrollTop;
        try {
          scroller.scrollTop = 0;
          await sleep(120);
          collectLinks();
          let steps = 0;
          while (scroller.scrollTop < scroller.scrollHeight - scroller.clientHeight - 4 && steps < 40 && found.size < 500) {
            scroller.scrollTop = Math.min(
              scroller.scrollHeight - scroller.clientHeight,
              scroller.scrollTop + Math.max(200, scroller.clientHeight * 0.8)
            );
            await sleep(160);
            collectLinks();
            steps++;
          }
          if (steps >= 40 || found.size >= 500) {
            if (scroller.scrollTop < scroller.scrollHeight - scroller.clientHeight - 4 || found.size >= 500) {
              truncated = true;
            }
          }
        } finally {
          scroller.scrollTop = originalTop;
        }
      }
    }
    collectLinks();
    return { provider, items: [...found.values()], truncated };
  }

  function visibleText(element) {
    if (!element || !element.isConnected) return "";
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    if (style.display === "none" || style.visibility === "hidden" || rect.width === 0 || rect.height === 0) return "";
    return (element.innerText || "").trim();
  }

  function messageNodes(provider) {
    if (provider === "chatgpt") {
      return [...document.querySelectorAll("[data-message-author-role]")];
    }
    if (provider === "gemini") {
      return [...document.querySelectorAll("user-query, model-response")];
    }
    const selectors = provider === "deepseek"
      ? ['[data-message-id]', '[data-testid*="message"]', 'div[class*="ds-message"]', 'div[class*="message"]']
      : provider === "qwen"
        ? ['[data-message-id]', '[data-testid*="message"]', 'div[class*="chat-message"]', 'div[class*="message-item"]', 'div[class*="message"]']
        : [
            '[data-testid="conversation-turn"]',
            '[data-testid*="message"]',
            '[data-message-id]'
          ];
    const nodes = selectors.flatMap(selector => [...document.querySelectorAll(selector)]);
    return [...new Set(nodes)].filter(node => !nodes.some(other => other !== node && node.contains(other)));
  }

  function roleFor(node, provider) {
    if (provider === "chatgpt") {
      const role = (node.getAttribute("data-message-author-role") || "").toLowerCase();
      return ["user", "assistant", "system", "tool"].includes(role) ? role : "unknown";
    }
    if (provider === "gemini") {
      const tag = node.tagName.toLowerCase();
      if (tag === "user-query") return "user";
      if (tag === "model-response") return "model";
    }
    const role = [
      node.getAttribute("data-message-author-role"),
      node.getAttribute("data-author"),
      node.getAttribute("data-role"),
      node.getAttribute("aria-label"),
      node.getAttribute("data-testid"),
      typeof node.className === "string" ? node.className : "",
      typeof node.parentElement?.className === "string" ? node.parentElement.className : ""
    ].filter(Boolean).join(" ").toLowerCase();
    if (/\b(user|you|human|prompt|query)\b/.test(role) || /justify-end|self-end/.test(role)) return "user";
    if (/\b(assistant|grok|deepseek|qwen|model|ai|response)\b/.test(role) || /justify-start|self-start/.test(role)) return "assistant";
    return "unknown";
  }

  function messageIdentity(node, role, content, index) {
    const explicit = node.getAttribute("data-message-id") || node.id;
    if (explicit) return explicit.slice(0, 180);
    // Text-derived IDs are only a fallback. collectVisible() detects a second
    // distinct DOM node with the same fallback ID and marks the capture ambiguous.
    let hash = 2166136261;
    const value = role + "\u0000" + content;
    for (let i = 0; i < value.length; i++) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return "visible-" + (hash >>> 0).toString(16);
  }

  function findScrollContainer(provider) {
    const messageAncestors = new Set();
    for (const node of messageNodes(provider)) {
      let parent = node.parentElement;
      for (let depth = 0; parent && depth < 10; depth++, parent = parent.parentElement) {
        messageAncestors.add(parent);
      }
    }
    const candidates = [
      ...messageAncestors,
      document.querySelector("main"),
      document.querySelector("[role='main']"),
      document.scrollingElement
    ].filter(Boolean);
    let best = document.scrollingElement;
    let score = 0;
    for (const element of candidates) {
      if (element.scrollHeight <= element.clientHeight + 80) continue;
      const style = getComputedStyle(element);
      if (!["auto", "scroll", "overlay"].includes(style.overflowY) && element !== document.scrollingElement) continue;
      const candidateScore = element.scrollHeight - element.clientHeight;
      if (candidateScore > score) {
        score = candidateScore;
        best = element;
      }
    }
    return best || document.scrollingElement;
  }

  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

  async function captureCurrentConversation() {
    const provider = providerForUrl(location.href);
    if (!provider) throw new Error("Provider is not allowed.");
    const sourceId = sourceIdForUrl(location.href, provider);
    if (!sourceId) throw new Error("This provider page does not expose a recognized conversation ID.");

    for (let attempt = 0; attempt < 12 && messageNodes(provider).length === 0; attempt++) {
      await sleep(500);
    }
    if (messageNodes(provider).length === 0) {
      throw new Error("Provider UI did not expose recognizable message containers.");
    }

    const scroller = findScrollContainer(provider);
    const originalTop = scroller.scrollTop;
    const collected = new Map();
    const orderedIds = [];
    const seenNodeObjects = new WeakSet();
    let sequenceOrderConflict = false;
    let steps = 0;
    let stableBottomRounds = 0;

    function mergeVisibleOrder(snapshotIds, phase) {
      const uniqueIds = [...new Set(snapshotIds)];
      if (!uniqueIds.length) return;
      if (!orderedIds.length) {
        orderedIds.push(...uniqueIds);
        return;
      }

      let index = 0;
      while (index < uniqueIds.length) {
        if (orderedIds.includes(uniqueIds[index])) {
          index++;
          continue;
        }

        const runStart = index;
        while (index < uniqueIds.length && !orderedIds.includes(uniqueIds[index])) {
          index++;
        }
        const newRun = uniqueIds.slice(runStart, index);
        const previousId = runStart > 0 ? uniqueIds[runStart - 1] : null;
        const nextId = index < uniqueIds.length ? uniqueIds[index] : null;
        const previousIndex = previousId ? orderedIds.indexOf(previousId) : -1;
        const nextIndex = nextId ? orderedIds.indexOf(nextId) : -1;

        if (previousIndex >= 0 && nextIndex >= 0) {
          if (previousIndex >= nextIndex) {
            sequenceOrderConflict = true;
            orderedIds.push(...newRun);
          } else {
            // Insert the newly observed turns into the gap between stable anchors.
            orderedIds.splice(nextIndex, 0, ...newRun);
          }
        } else if (previousIndex >= 0) {
          orderedIds.splice(previousIndex + 1, 0, ...newRun);
        } else if (nextIndex >= 0) {
          orderedIds.splice(nextIndex, 0, ...newRun);
        } else if (phase === "top") {
          // A disjoint top snapshot is an older history window.
          orderedIds.unshift(...newRun);
        } else {
          // A disjoint downward-scroll snapshot is later in the conversation.
          orderedIds.push(...newRun);
        }
      }
    }
    function collectVisible(phase) {
      const nodes = messageNodes(provider);
      const snapshotIds = [];
      for (let index = 0; index < nodes.length; index++) {
        const node = nodes[index];
        const content = visibleText(node);
        if (!content) continue;
        const role = roleFor(node, provider);
        const explicitId = node.getAttribute("data-message-id") || node.id;
        const id = messageIdentity(node, role, content, collected.size + index);
        snapshotIds.push(id);
        const repeatedNodeObject = seenNodeObjects.has(node);
        seenNodeObjects.add(node);
        if (collected.has(id) && !explicitId && !repeatedNodeObject) {
          // Identical text-only turns cannot be distinguished from a virtualized
          // duplicate without a provider message ID. Preserve the snapshot but
          // mark it truncated rather than silently claiming every turn survived.
          sequenceOrderConflict = true;
        }
        if (!collected.has(id)) {
          collected.set(id, {
            message_id: id,
            role,
            content: content.slice(0, 100000),
            timestamp: node.querySelector("time[datetime]")?.getAttribute("datetime") || null
          });
        }
      }
      mergeVisibleOrder(snapshotIds, phase);
    }
    let topLoadSteps = 0;
    let topLoadLimitReached = false;
    try {
      // Virtualized providers may fetch older turns only after the top boundary
      // remains active for several render cycles. A single scrollTop=0 is not
      // sufficient evidence that the oldest messages have loaded.
      scroller.scrollTop = 0;
      await sleep(350);
      collectVisible("top");
      let stableTopRounds = 0;
      let previousTopHeight = scroller.scrollHeight;
      let previousTopMessageCount = collected.size;
      while (topLoadSteps < 20 && stableTopRounds < 4) {
        scroller.scrollTop = 0;
        await sleep(500);
        collectVisible("top");
        const currentHeight = scroller.scrollHeight;
        const currentMessageCount = collected.size;
        if (currentHeight > previousTopHeight || currentMessageCount > previousTopMessageCount) {
          stableTopRounds = 0;
        } else {
          stableTopRounds++;
        }
        previousTopHeight = currentHeight;
        previousTopMessageCount = currentMessageCount;
        topLoadSteps++;
      }
      if (stableTopRounds < 3) topLoadLimitReached = true;
      while (steps < 100) {
        const before = scroller.scrollTop;
        const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
        if (before >= max - 4) {
          stableBottomRounds++;
          if (stableBottomRounds >= 2) break;
        } else {
          stableBottomRounds = 0;
          scroller.scrollTop = Math.min(max, before + Math.max(300, scroller.clientHeight * 0.75));
        }
        await sleep(250);
        collectVisible("scroll");
        steps++;
      }
    } finally {
      scroller.scrollTop = originalTop;
    }

    if (!collected.size) throw new Error("No message containers were recognized; nothing was archived.");
    // Merge each DOM window against stable message IDs. Overlapping IDs
    // establish a relative offset; disjoint top windows are older and prepend,
    // while disjoint downward-scroll windows append. Ambiguous overlaps mark
    // the capture truncated instead of asserting a trustworthy sequence.
    const messages = orderedIds
      .map(id => collected.get(id))
      .filter(Boolean);
    messages.forEach((message, index) => { message.sequence = index; });
    if (messages.length !== collected.size) sequenceOrderConflict = true;
    const unknownRoleCount = messages.filter(message => message.role === "unknown").length;
    return {
      provider,
      source_id: sourceId,
      title: conversationTitle(null, location.href),
      url: location.href,
      messages,
      truncated: steps >= 100 || topLoadLimitReached || sequenceOrderConflict,
      // Reaching the current DOM top is not proof of oldest provider history.
      history_start_reached: false,
      oldest_boundary: "unknown",
      oldest_boundary_evidence: "",
      messages_total: messages.length,
      unknown_role_count: unknownRoleCount,
      scroll_steps: steps,
      top_load_steps: topLoadSteps,
      top_load_limit_reached: topLoadLimitReached,
      sequence_order_conflict: sequenceOrderConflict,
      adapter_version: VERSION,
      captured_at: new Date().toISOString()
    };
  }

  function findComposer(provider) {
    const selectors = provider === "chatgpt"
      ? ["#prompt-textarea", '[data-testid="prompt-textarea"]', 'textarea[placeholder]', '[contenteditable="true"].ProseMirror']
      : provider === "gemini"
        ? ["rich-textarea [contenteditable='true']", ".ql-editor[contenteditable='true']", "textarea"]
        : provider === "deepseek"
          ? ["textarea[placeholder]", "textarea", '[contenteditable="true"]', '[contenteditable="true"].ProseMirror']
          : provider === "qwen"
            ? ["textarea[placeholder]", "textarea", '[contenteditable="true"]', '[contenteditable="true"].ProseMirror']
            : ["textarea[placeholder]", 'textarea', '[contenteditable="true"][data-placeholder]', '[contenteditable="true"].ProseMirror'];
    for (const selector of selectors) {
      for (const node of document.querySelectorAll(selector)) {
        const rect = node.getBoundingClientRect();
        const style = getComputedStyle(node);
        if (node.isConnected && rect.width > 0 && rect.height > 0 &&
            style.display !== "none" && style.visibility !== "hidden" &&
            !node.disabled && node.getAttribute("aria-disabled") !== "true") return node;
      }
    }
    return null;
  }

  function setComposerText(composer, text) {
    composer.focus();
    if (composer instanceof HTMLTextAreaElement || composer instanceof HTMLInputElement) {
      const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(composer), "value")?.set;
      if (!setter) throw new Error("The provider text field cannot be updated safely.");
      setter.call(composer, text);
      composer.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
      composer.dispatchEvent(new Event("change", { bubbles: true }));
    } else {
      composer.replaceChildren();
      composer.textContent = text;
      composer.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
    }
  }

  function findSendButton(provider, composer) {
    const selectors = [
      'button[data-testid="send-button"]',
      'button[aria-label*="Send" i]',
      'button[aria-label*="Enviar" i]',
      'button[title*="Send" i]',
      'button[title*="Enviar" i]',
      'button[aria-label*="发送" i]',
      'button[title*="发送" i]',
      'button[aria-label*="提交" i]',
      'button[title*="提交" i]'
    ];
    for (const selector of selectors) {
      for (const button of document.querySelectorAll(selector)) {
        const rect = button.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && !button.disabled &&
            button.getAttribute("aria-disabled") !== "true") return button;
      }
    }
    const form = composer.closest("form");
    if (form) {
      const button = form.querySelector('button[type="submit"]');
      if (button && !button.disabled && button.getAttribute("aria-disabled") !== "true") return button;
    }
    return null;
  }

  async function sendMessageThroughVisibleUi(request) {
    const provider = providerForUrl(location.href);
    if (!provider) throw new Error("This tab is not an allowed AI provider.");
    const sourceId = sourceIdForUrl(location.href, provider);
    if (!sourceId) throw new Error("Open an existing conversation before sending.");
    if (request.source_id && request.source_id !== sourceId) {
      throw new Error("The active conversation changed; message was not sent.");
    }
    const text = String(request.text || "");
    if (!text.trim() || text.length > 30000) throw new Error("Message must contain 1–30000 characters.");
    const blocked = detectBlockedPage();
    if (blocked) throw new Error("Provider blocked: " + blocked + ". Message was not sent.");
    const composer = findComposer(provider);
    if (!composer) throw new Error("No supported visible message composer was found.");
    setComposerText(composer, text);
    await sleep(150);
    const currentText = (composer.value ?? composer.innerText ?? composer.textContent ?? "").trim();
    if (currentText !== text.trim()) throw new Error("Composer verification failed; message was not sent.");
    const sendButton = findSendButton(provider, composer);
    if (!sendButton) throw new Error("No enabled provider Send button was found; message was not sent.");
    sendButton.click();
    const deadline = Date.now() + 12000;
    let observed = false;
    while (Date.now() < deadline) {
      await sleep(300);
      const found = messageNodes(provider).some(node =>
        roleFor(node, provider) === "user" && visibleText(node).trim().includes(text.trim())
      );
      if (found) { observed = true; break; }
    }
    return {
      provider,
      source_id: sourceId,
      status: observed ? "submitted_and_visible" : "submitted_unverified",
      verification: observed ? "user_message_observed_in_conversation" : "send_clicked_but_message_not_observed",
      sent_at: new Date().toISOString()
    };
  }


  async function executeBrowserOperatorTask(request) {
    const provider = providerForUrl(location.href);
    if (!provider || provider !== request.provider) throw new Error("Active provider does not match the queued task.");
    const sourceId = sourceIdForUrl(location.href, provider);
    if (!sourceId || sourceId !== request.source_id) throw new Error("Active conversation does not match the queued task.");
    const initialBlock = detectBlockedPage();
    if (initialBlock) {
      return { provider, source_id: sourceId, status: "blocked",
        reason: initialBlock, assistant_text: "", sent_status: "not_sent" };
    }
    const sent = await sendMessageThroughVisibleUi({
      text: request.message,
      source_id: request.source_id
    });
    if (sent.status !== "submitted_and_visible") {
      return { ...sent, status: "unverified", assistant_text: "", reason: "user_message_not_verified" };
    }

    const timeoutMs = Math.max(1000, Math.min(Number(request.response_timeout_ms) || 120000, 180000));
    const deadline = Date.now() + timeoutMs;
    let previousText = "";
    let stableRounds = 0;
    while (Date.now() < deadline) {
      const blocked = detectBlockedPage();
      if (blocked) {
        return {
          provider, source_id: sourceId, status: "blocked",
          reason: blocked, assistant_text: "", sent_status: sent.status
        };
      }
      const nodes = messageNodes(provider);
      const userIndex = nodes.findIndex(node =>
        roleFor(node, provider) === "user" &&
        visibleText(node).trim().includes(String(request.message).trim())
      );
      if (userIndex >= 0) {
        const assistant = nodes.slice(userIndex + 1).filter(node =>
          ["assistant", "model"].includes(roleFor(node, provider))
        );
        const candidate = assistant.length ? visibleText(assistant[assistant.length - 1]) : "";
        if (candidate && candidate === previousText) stableRounds++;
        else stableRounds = candidate ? 1 : 0;
        previousText = candidate;
        if (candidate && stableRounds >= 5) {
          return {
            provider, source_id: sourceId, status: "completed",
            assistant_text: candidate.slice(0, 100000),
            sent_status: sent.status,
            verification: "assistant_response_observed_stable"
          };
        }
      }
      await sleep(1000);
    }
    return {
      provider, source_id: sourceId, status: "unverified",
      assistant_text: previousText.slice(0, 100000),
      sent_status: sent.status,
      reason: "assistant_response_timeout"
    };
  }

  let freshReviewState = null;

  function freshReviewPrivacyMode(provider) {
    const bodyText = String(document.body?.innerText || "").toLowerCase();
    const controls = [...document.querySelectorAll("button, [role='button'], [aria-label], [title]")];
    const labels = controls.map(node => [
      node.innerText,
      node.getAttribute("aria-label"),
      node.getAttribute("title")
    ].filter(Boolean).join(" ")).join(" ").toLowerCase();
    const activeControls = controls.filter(node => {
      const state = [
        node.getAttribute("aria-pressed"),
        node.getAttribute("aria-checked"),
        node.getAttribute("aria-selected"),
        node.getAttribute("data-state"),
        node.getAttribute("data-checked")
      ].map(value => String(value || "").toLowerCase());
      return state.some(value => ["true", "on", "checked", "selected"].includes(value));
    });
    const activeLabels = activeControls.map(node => [
      node.innerText,
      node.getAttribute("aria-label"),
      node.getAttribute("title")
    ].filter(Boolean).join(" ")).join(" ").toLowerCase();
    // Labels alone are not proof: settings menus can display disabled options.
    // Require the provider UI to expose an explicit active/checked state.
    if (provider === "chatgpt" &&
        /temporary(?:\\s+chat)?/.test(activeLabels) &&
        /unpersonalized|without personalization|sem personaliza/.test(activeLabels)) {
      return "chatgpt_temporary_unpersonalized";
    }
    if (provider === "gemini" && /temporary\\s+chat/.test(activeLabels)) {
      return "gemini_temporary_chat";
    }
    // Grok Private Chat is not enough by itself: its separate X-personalization
    // setting must also be confirmed off. DeepSeek/Qwen have no verified
    // provider UI temporary-mode contract in this adapter.
    return "";
  }

  function freshReviewPreflight() {
    const provider = providerForUrl(location.href);
    if (!provider) return { ok: false, fresh_review_ready: false, reason: "provider_not_allowed" };
    const blocked = detectBlockedPage();
    if (blocked) return { ok: false, fresh_review_ready: false, provider, reason: blocked };
    const privacyMode = freshReviewPrivacyMode(provider);
    if (!privacyMode) {
      freshReviewState = null;
      return { ok: false, fresh_review_ready: false, provider, reason: "provider_privacy_mode_not_verified" };
    }
    if (sourceIdForUrl(location.href, provider)) {
      freshReviewState = null;
      return { ok: false, fresh_review_ready: false, provider, reason: "existing_conversation_detected" };
    }
    const priorMessages = messageNodes(provider).filter(node => {
      const role = roleFor(node, provider);
      return ["user", "assistant", "model"].includes(role) && Boolean(visibleText(node));
    });
    if (priorMessages.length) {
      freshReviewState = null;
      return { ok: false, fresh_review_ready: false, provider, reason: "visible_prior_messages_detected" };
    }
    if (!findComposer(provider)) {
      freshReviewState = null;
      return { ok: false, fresh_review_ready: false, provider, reason: "visible_composer_not_found" };
    }
    const nonce = Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 14);
    freshReviewState = { provider, url: location.href, nonce, privacyMode };
    return {
      ok: true,
      fresh_review_ready: true,
      provider,
      preflight_nonce: nonce,
      initial_source_id: null,
      initial_visible_message_count: 0,
      evidence_kind: "visible_blank_temporary_provider_page",
      privacy_mode: privacyMode,
      privacy_mode_verified: true,
      independence_attested: false
    };
  }

  async function executeFreshReviewTask(request) {
    const armed = freshReviewState;
    freshReviewState = null; // one-shot: even a failed attempt must be explicitly re-armed.
    const provider = providerForUrl(location.href);
    if (!armed || !request || request.preflight_nonce !== armed.nonce) {
      throw new Error("Fresh-review preflight is missing, expired or mismatched.");
    }
    if (provider !== armed.provider || request.provider !== armed.provider || location.href !== armed.url) {
      throw new Error("Provider tab changed after fresh-review preflight; nothing was sent.");
    }
    if (freshReviewPrivacyMode(provider) !== armed.privacyMode) {
      throw new Error("Provider privacy mode changed or is no longer verifiable; nothing was sent.");
    }
    if (sourceIdForUrl(location.href, provider)) {
      throw new Error("An existing conversation appeared after preflight; nothing was sent.");
    }
    const priorMessages = messageNodes(provider).filter(node => {
      const role = roleFor(node, provider);
      return ["user", "assistant", "model"].includes(role) && Boolean(visibleText(node));
    });
    if (priorMessages.length) {
      throw new Error("Prior visible messages appeared after preflight; nothing was sent.");
    }
    const text = String(request.message || "");
    if (!text.trim() || text.length > 8000) {
      throw new Error("Fresh-review message must contain 1–8000 characters.");
    }
    const blocked = detectBlockedPage();
    if (blocked) return {
      provider, status: "blocked", reason: blocked, assistant_text: "",
      fresh_context_observed: false, independence_attested: false
    };
    const composer = findComposer(provider);
    if (!composer) throw new Error("No supported visible composer is available.");
    setComposerText(composer, text);
    await sleep(150);
    const currentText = (composer.value ?? composer.innerText ?? composer.textContent ?? "").trim();
    if (currentText !== text.trim()) throw new Error("Fresh-review composer verification failed.");
    const sendButton = findSendButton(provider, composer);
    if (!sendButton) throw new Error("No enabled provider Send button was found.");
    sendButton.click();

    const timeoutMs = Math.max(1000, Math.min(Number(request.response_timeout_ms) || 120000, 180000));
    const deadline = Date.now() + timeoutMs;
    let newSourceId = null;
    let userObserved = false;
    while (Date.now() < deadline) {
      const pageBlock = detectBlockedPage();
      if (pageBlock) return {
        provider, status: "blocked", reason: pageBlock, assistant_text: "",
        fresh_context_observed: false, independence_attested: false
      };
      newSourceId = sourceIdForUrl(location.href, provider);
      userObserved = messageNodes(provider).some(node =>
        roleFor(node, provider) === "user" && visibleText(node).trim().includes(text.trim())
      );
      if (newSourceId && userObserved) break;
      await sleep(300);
    }
    if (!newSourceId || !userObserved) {
      return {
        provider, status: "unverified", reason: "new_conversation_not_observed",
        assistant_text: "", fresh_context_observed: false, independence_attested: false
      };
    }

    let previousText = "";
    let stableRounds = 0;
    while (Date.now() < deadline) {
      const pageBlock = detectBlockedPage();
      if (pageBlock) return {
        provider, source_id: newSourceId, status: "blocked", reason: pageBlock,
        assistant_text: "", fresh_context_observed: true, independence_attested: false
      };
      const nodes = messageNodes(provider);
      const userIndex = nodes.findIndex(node =>
        roleFor(node, provider) === "user" && visibleText(node).trim().includes(text.trim())
      );
      if (userIndex >= 0) {
        const assistant = nodes.slice(userIndex + 1).filter(node =>
          ["assistant", "model"].includes(roleFor(node, provider))
        );
        const candidate = assistant.length ? visibleText(assistant[assistant.length - 1]) : "";
        if (candidate && candidate === previousText) stableRounds++;
        else stableRounds = candidate ? 1 : 0;
        previousText = candidate;
        if (candidate && stableRounds >= 5) {
          return {
            provider,
            source_id: newSourceId,
            status: "completed",
            assistant_text: candidate.slice(0, 16000),
            fresh_context_observed: true,
            privacy_mode: armed.privacyMode,
            privacy_mode_verified: true,
            initial_source_id: null,
            initial_visible_message_count: 0,
            verification: "blank_page_then_new_conversation_id_and_stable_response",
            independence_attested: false
          };
        }
      }
      await sleep(1000);
    }
    return {
      provider, source_id: newSourceId, status: "unverified",
      reason: "assistant_response_timeout",
      assistant_text: previousText.slice(0, 16000),
      fresh_context_observed: true,
      independence_attested: false
    };
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "DGM_FRESH_REVIEW_PING") {
      sendResponse(freshReviewPreflight());
      return false;
    }
    if (message?.type === "DGM_EXECUTE_FRESH_REVIEW") {
      executeFreshReviewTask(message)
        .then(data => sendResponse({ ok: true, data }))
        .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
      return true;
    }
    if (message?.type === "DGM_PROVIDER_PING") {
      const provider = providerForUrl(location.href);
      sendResponse({
        ok: Boolean(provider),
        provider,
        source_id: provider ? sourceIdForUrl(location.href, provider) : null,
        blocked: detectBlockedPage()
      });
      return false;
    }
    if (message.type === "DGM_EXECUTE_BROWSER_TASK") {
      executeBrowserOperatorTask(message)
        .then(data => sendResponse({ ok: true, data }))
        .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
      return true;
    }

    if (!message || typeof message.type !== "string") return false;
    if (message.type === "DGM_DISCOVER_VISIBLE") {
      discoverConversations()
        .then(data => sendResponse({ ok: true, data }))
        .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
      return true;
    }
    if (message.type === "DGM_CAPTURE_CURRENT") {
      captureCurrentConversation()
        .then(data => sendResponse({ ok: true, data }))
        .catch(error => sendResponse({ ok: false, error: String(error.message || error) }));
      return true;
    }
    if (message.type === "DGM_NAVIGATE_TO") {
      try {
        const provider = providerForUrl(location.href);
        const target = new URL(message.url, location.href);
        if (!provider || providerForUrl(target.href) !== provider || target.origin !== location.origin ||
            !isConversationUrl(target.href, provider)) {
          throw new Error("Navigation target is outside the current provider conversation allowlist.");
        }
        sendResponse({ ok: true });
        setTimeout(() => location.assign(target.href), 50);
      } catch (error) {
        sendResponse({ ok: false, error: String(error.message || error) });
      }
      return false;
    }
    return false;
  });

  function detectBlockedPage() {
    const path = location.pathname.toLowerCase();
    const text = (document.body?.innerText || "").slice(0, 12000).toLowerCase();
    if (/\/(?:auth|login|signin|sign-in)(?:\/|$)/.test(path) ||
        /sign in to continue|log in to continue|session expired|please sign in/.test(text)) {
      return "blocked_login";
    }
    if (/captcha|verify you are human|unusual traffic|security challenge/.test(text)) {
      return "blocked_challenge";
    }
    if (/too many requests|rate limit|try again later|quota exceeded|daily quota|usage limit|message limit|you(?:'ve| have) reached (?:your )?.{0,50}limit|limit reached|limite de mensagens|limite diário|atingiste o limite|atingiu o limite|cota excedida/.test(text)) {
      return "rate_limited";
    }
    return "";
  }

  // Notify the service worker after every provider-page load. It only acts when
  // the operator explicitly started a recovery run in this tab.
  const readyProvider = providerForUrl(location.href);
  chrome.runtime.sendMessage({
    type: "DGM_PROVIDER_PAGE_READY",
    url: location.href,
    provider: readyProvider,
    source_id: readyProvider ? sourceIdForUrl(location.href, readyProvider) : null,
    blocked: detectBlockedPage()
  }).catch(() => {});
})();
