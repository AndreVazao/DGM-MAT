(() => {
  "use strict";

  const VERSION = "0.1.0";
  const PROVIDER_HOSTS = {
    chatgpt: new Set(["chatgpt.com", "chat.openai.com"]),
    gemini: new Set(["gemini.google.com"]),
    grok: new Set(["grok.com", "x.com"])
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
    } catch (_) {}
    return null;
  }

  function sourceIdForUrl(value, provider) {
    const url = new URL(value);
    if (provider === "chatgpt") {
      const match = url.pathname.match(/\/c\/([A-Za-z0-9_-]+)/);
      return match ? match[1] : null;
    }
    if (provider === "gemini") {
      const match = url.pathname.match(/\/app\/([A-Za-z0-9_-]+)/);
      return match ? match[1] : null;
    }
    const queryId = url.searchParams.get("conversation") || url.searchParams.get("id");
    if (queryId && /^[A-Za-z0-9._:-]{1,200}$/.test(queryId)) return queryId;
    const match = url.pathname.match(/\/(?:chat|c|i\/grok)\/([A-Za-z0-9_-]+)/);
    return match ? match[1] : null;
  }

  function conversationTitle(anchor, url) {
    const text = (anchor?.innerText || anchor?.getAttribute("aria-label") || "").trim();
    if (text) return text.slice(0, 500);
    const title = (document.title || "").replace(/\s*[|—-]\s*(ChatGPT|Gemini|Grok).*$/i, "").trim();
    return title.slice(0, 500) || "Conversation " + url.pathname.split("/").filter(Boolean).pop();
  }

  function isConversationUrl(value, provider) {
    const id = sourceIdForUrl(value, provider);
    if (!id) return false;
    const url = new URL(value);
    if (provider === "grok" && url.hostname === "x.com" && !url.pathname.startsWith("/i/grok")) return false;
    return true;
  }

  function discoverConversations() {
    const provider = providerForUrl(location.href);
    if (!provider) throw new Error("This tab is not an allowed AI provider page.");
    const found = new Map();

    if (isConversationUrl(location.href, provider)) {
      const id = sourceIdForUrl(location.href, provider);
      found.set(id, {
        source_id: id,
        title: conversationTitle(null, location.href),
        url: location.href,
        source_date: "unknown-date"
      });
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
    return { provider, items: [...found.values()] };
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
    const selectors = [
      '[data-testid="conversation-turn"]',
      '[data-testid*="message"]',
      '[data-message-id]'
    ];
    const nodes = selectors.flatMap(selector => [...document.querySelectorAll(selector)]);
    return [...new Set(nodes)].filter(node => !nodes.some(other => other !== node && other.contains(node)));
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
      node.getAttribute("aria-label")
    ].filter(Boolean).join(" ").toLowerCase();
    if (/\b(user|you)\b/.test(role)) return "user";
    if (/\b(assistant|grok|model|ai)\b/.test(role)) return "assistant";
    return "unknown";
  }

  function messageIdentity(node, role, content, index) {
    const explicit = node.getAttribute("data-message-id") || node.id;
    if (explicit) return explicit.slice(0, 180);
    // Text-derived IDs are stable across scroll windows; duplicate identical turns
    // remain a documented selector limitation until provider DOM IDs are available.
    let hash = 2166136261;
    const value = role + "\u0000" + content;
    for (let i = 0; i < value.length; i++) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return "visible-" + (hash >>> 0).toString(16);
  }

  function findScrollContainer() {
    const candidates = [document.scrollingElement, ...document.querySelectorAll("main, [role='main'], div")].filter(Boolean);
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

    const scroller = findScrollContainer();
    const originalTop = scroller.scrollTop;
    const collected = new Map();
    let sequence = 0;
    let steps = 0;
    let stableBottomRounds = 0;

    function collectVisible() {
      const nodes = messageNodes(provider);
      for (const node of nodes) {
        const content = visibleText(node);
        if (!content) continue;
        const role = roleFor(node, provider);
        const id = messageIdentity(node, role, content, sequence++);
        if (!collected.has(id)) {
          collected.set(id, {
            message_id: id,
            role,
            content: content.slice(0, 100000),
            sequence: collected.size,
            timestamp: null
          });
        }
      }
    }

    try {
      scroller.scrollTop = 0;
      await sleep(350);
      collectVisible();
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
        collectVisible();
        steps++;
      }
    } finally {
      scroller.scrollTop = originalTop;
    }

    if (!collected.size) throw new Error("No message containers were recognized; nothing was archived.");
    const messages = [...collected.values()];
    messages.forEach((message, index) => { message.sequence = index; });
    return {
      provider,
      source_id: sourceId,
      title: conversationTitle(null, location.href),
      url: location.href,
      messages,
      truncated: steps >= 100,
      history_start_reached: true,
      adapter_version: VERSION,
      captured_at: new Date().toISOString()
    };
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || typeof message.type !== "string") return false;
    if (message.type === "DGM_DISCOVER_VISIBLE") {
      try { sendResponse({ ok: true, data: discoverConversations() }); }
      catch (error) { sendResponse({ ok: false, error: String(error.message || error) }); }
      return false;
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

  // Notify the service worker after every provider-page load. It only acts when
  // the operator explicitly started a recovery run in this tab.
  chrome.runtime.sendMessage({
    type: "DGM_PROVIDER_PAGE_READY",
    url: location.href,
    provider: providerForUrl(location.href)
  }).catch(() => {});
})();
