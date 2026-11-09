"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "../../browser_extension/content.js"),
  "utf8"
);

function makeMessage(
  index,
  role = index % 2 === 0 ? "user" : "assistant",
  options = {},
  provider = "chatgpt"
) {
  const text = options.text || "Fixture turn " + index;
  return {
    id: "",
    tagName: provider === "gemini"
      ? (role === "user" ? "USER-QUERY" : "MODEL-RESPONSE")
      : "DIV",
    className: "",
    parentElement: null,
    isConnected: true,
    innerText: text,
    contains(other) { return Array.isArray(options.children) && options.children.includes(other); },
    getAttribute(name) {
      if (name === "data-message-id") return options.explicitId === false ? null : "message-" + index;
      if (name === "data-message-author-role") return role;
      if (name === "data-testid") return options.testId || (provider === "claude" ? role + "-message" : "conversation-turn");
      return null;
    },
    getBoundingClientRect() {
      return { width: 640, height: 40 };
    },
    querySelector() {
      return null;
    }
  };
}

function createHarness(mode, provider = "chatgpt", bodyText = "", urlOverride = null) {
  const all = Array.from({ length: 12 }, (_, index) => makeMessage(index, undefined, {}, provider));
  const nestedClaudeMessage = provider === "claude" ? makeMessage(99, "user", { text: "Nested Claude turn" }, provider) : null;
  const nestedClaudeWrapper = provider === "claude" ? makeMessage(100, "assistant", {
    text: "Wrapper text", testId: "chat-message", children: [nestedClaudeMessage]
  }, provider) : null;
  const ambiguousFirst = makeMessage(50, "user", {
    text: "Repeated identical text-only turn",
    explicitId: false
  }, provider);
  const ambiguousSecond = makeMessage(51, "user", {
    text: "Repeated identical text-only turn",
    explicitId: false
  }, provider);
  let visible = mode === "dom-mismatch" ? [] : mode === "ambiguous-duplicate" ? [ambiguousFirst]
    : mode === "claude-nested" ? [nestedClaudeWrapper, nestedClaudeMessage] : all.slice(6, 10);
  let olderLoaded = false;
  let topWaits = 0;
  let listener = null;
  let pageReadyMessage = null;
  let scrollCalls = 0;

  function updateVisible(top) {
    if (mode === "dom-mismatch") {
      visible = [];
      return;
    }
    if (mode === "ambiguous-duplicate") {
      visible = topWaits >= 1 ? [ambiguousSecond] : [ambiguousFirst];
      return;
    }
    if (mode === "multi-window") {
      if (!olderLoaded) {
        visible = all.slice(6, 10);
      } else if (top < 100) {
        visible = all.slice(0, 5);
      } else if (top < 500) {
        visible = all.slice(3, 8);
      } else if (top < 900) {
        visible = all.slice(6, 11);
      } else {
        visible = all.slice(8, 12);
      }
      return;
    }
    if (top < 100) visible = all.slice(4, 8);
    else if (top < 900) visible = all.slice(6, 11);
    else visible = all.slice(8, 12);
  }

  const scroller = {
    clientHeight: 500,
    scrollHeight: 1000,
    _scrollTop: 0,
    get scrollTop() {
      return this._scrollTop;
    },
    set scrollTop(value) {
      this._scrollTop = value;
      scrollCalls++;
      updateVisible(value);
    }
  };

  const document = {
    title: "Virtualized history fixture | ChatGPT",
    body: { innerText: bodyText },
    scrollingElement: scroller,
    querySelector() {
      return null;
    },
    querySelectorAll(selector) {
      if (provider === "chatgpt" && selector === "[data-message-author-role]") return visible;
      if (provider === "gemini" && selector === "user-query, model-response") return visible;
      if (provider === "claude" && selector === '[data-testid="user-message"], [data-testid="assistant-message"], [data-testid="chat-message"]') return visible;
      if (provider === "grok" && [
        '[data-testid="conversation-turn"]',
        '[data-testid*="message"]',
        '[data-message-id]'
      ].includes(selector)) return visible;
      if (["deepseek", "qwen"].includes(provider) && [
        '[data-message-id]', '[data-testid*="message"]', 'div[class*="ds-message"]',
        'div[class*="chat-message"]', 'div[class*="message-item"]', 'div[class*="message"]'
      ].includes(selector)) return visible;
      return [];
    }
  };

  const sandbox = {
    URL,
    Map,
    Set,
    Promise,
    Math,
    Date,
    Error,
    String,
    Array,
    Object,
    RegExp,
    Number,
    JSON,
    document,
    location: {
      href: urlOverride || {
        chatgpt: "https://chatgpt.com/c/fixture-conversation",
        gemini: "https://gemini.google.com/app/fixture-conversation",
        grok: "https://grok.com/chat/fixture-conversation",
        deepseek: "https://chat.deepseek.com/a/chat/s/fixture-conversation",
        qwen: "https://chat.qwen.ai/chat/fixture-conversation",
        claude: "https://claude.ai/chat/fixture-conversation"
      }[provider],
      pathname: new URL(urlOverride || ({
        chatgpt: "https://chatgpt.com/c/fixture-conversation",
        gemini: "https://gemini.google.com/app/fixture-conversation",
        grok: "https://grok.com/chat/fixture-conversation",
        deepseek: "https://chat.deepseek.com/a/chat/s/fixture-conversation",
        qwen: "https://chat.qwen.ai/chat/fixture-conversation",
        claude: "https://claude.ai/chat/fixture-conversation"
      }[provider])).pathname,
      assign() {
        throw new Error("Navigation is not expected during capture tests.");
      }
    },
    getComputedStyle() {
      return { display: "block", visibility: "visible", overflowY: "auto" };
    },
    chrome: {
      runtime: {
        onMessage: {
          addListener(callback) {
            listener = callback;
          }
        },
        sendMessage(message) {
          pageReadyMessage = message;
          return Promise.resolve({ ok: true });
        }
      }
    },
    setTimeout(callback, milliseconds) {
      if (milliseconds === 500) {
        topWaits++;
        if (mode === "ambiguous-duplicate" && topWaits === 1) {
          visible = [ambiguousSecond];
        }
        if (mode === "multi-window" && topWaits === 2) {
          olderLoaded = true;
          scroller.scrollHeight += 500;
          updateVisible(0);
        } else if (mode === "top-limit") {
          // Simulate an endless provider that keeps extending the top window.
          scroller.scrollHeight += 100;
        }
      }
      if (milliseconds === 250 && mode === "scroll-limit" && scroller.scrollTop > 0) {
        // Simulate a page that keeps appending content as the user scrolls.
        scroller.scrollHeight += 2000;
      }
      callback();
      return 1;
    }
  };

  vm.runInNewContext(source, sandbox, { filename: "browser_extension/content.js" });
  assert.equal(typeof listener, "function", "content script must register its message listener");

  async function capture() {
    return await new Promise(resolve => {
      const accepted = listener(
        { type: "DGM_CAPTURE_CURRENT" },
        {},
        response => resolve(response)
      );
      assert.equal(accepted, true, "capture listener must keep the response channel open");
    });
  }

  return { capture, getScrollCalls: () => scrollCalls, getPageReadyMessage: () => pageReadyMessage };
}

async function testVirtualizedHistoryWindowsAndDuplicates() {
  const harness = createHarness("multi-window");
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  const data = response.data;

  assert.equal(data.messages_total, 12, "all historical windows must be recovered");
  assert.deepEqual(
    Array.from(data.messages, message => message.message_id),
    Array.from({ length: 12 }, (_, index) => "message-" + index),
    "captured sequence must remain chronological across reversed top-loading windows"
  );
  assert.deepEqual(
    Array.from(data.messages, message => message.sequence),
    Array.from({ length: 12 }, (_, index) => index)
  );
  assert.equal(new Set(data.messages.map(message => message.message_id)).size, 12,
    "overlapping windows must not duplicate turns");
  assert.equal(data.history_start_reached, false,
    "reaching the rendered top must never imply oldest provider history");
  assert.equal(data.oldest_boundary, "unknown",
    "no provider-confirmed oldest marker exists in this fixture");
  assert.equal(data.oldest_boundary_evidence, "");
  assert.equal(data.truncated, false);
  assert.equal(data.sequence_order_conflict, false);
  assert.ok(data.top_load_steps >= 2);
  assert.ok(harness.getScrollCalls() > 0);
}

async function testProviderScopedSelectorsRemainSupported() {
  for (const provider of ["chatgpt", "gemini", "grok", "deepseek", "qwen", "claude"]) {
    const harness = createHarness("no-oldest-marker", provider);
    const response = await harness.capture();
    assert.equal(response.ok, true, provider + ": " + response.error);
    assert.equal(response.data.provider, provider);
    assert.ok(response.data.messages_total > 0);
    if (provider === "gemini") {
      assert.ok(response.data.messages.every(message => ["user", "model"].includes(message.role)));
    } else {
      assert.ok(response.data.messages.every(message => ["user", "assistant"].includes(message.role)));
    }
    assert.equal(response.data.history_start_reached, false);
    assert.equal(response.data.oldest_boundary, "unknown");
  }
}

async function testClaudeProjectConversationRouteUsesConversationId() {
  const harness = createHarness(
    "no-oldest-marker",
    "claude",
    "",
    "https://claude.ai/project/project-12345678/chat/conversation-87654321"
  );
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.provider, "claude");
  assert.equal(response.data.source_id, "conversation-87654321",
    "project route must use the chat ID, not the project ID");
}

async function testClaudeNestedMessageWrappersAreNotDuplicated() {
  const harness = createHarness("claude-nested", "claude");
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.messages_total, 1,
    "nested chat-message wrapper and user-message child must produce one archived turn");
  assert.equal(response.data.messages[0].content, "Nested Claude turn");
  assert.equal(response.data.messages[0].role, "user");
}

async function testClaudeNonConversationRoutesFailClosed() {
  for (const url of [
    "https://claude.ai/new",
    "https://claude.ai/project/project-12345678",
    "https://claude.ai/chat"
  ]) {
    const harness = createHarness("no-oldest-marker", "claude", "", url);
    const response = await harness.capture();
    assert.equal(response.ok, false, url + " must not be treated as a conversation");
    assert.match(response.error, /recognized conversation ID/);
  }
}

async function testMissingOldestMarkerRemainsPartialOrUnknown() {
  const harness = createHarness("no-oldest-marker");
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.history_start_reached, false);
  assert.equal(response.data.oldest_boundary, "unknown");
  assert.equal(response.data.truncated, false);
}

async function testTopLoadingHardLimitIsExplicitlyTruncated() {
  const harness = createHarness("top-limit");
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.top_load_steps, 20);
  assert.equal(response.data.top_load_limit_reached, true);
  assert.equal(response.data.truncated, true);
  assert.equal(response.data.history_start_reached, false);
  assert.equal(response.data.oldest_boundary, "unknown");
}

async function testProviderDomMismatchFailsClosed() {
  const harness = createHarness("dom-mismatch", "chatgpt");
  const response = await harness.capture();
  assert.equal(response.ok, false);
  assert.match(response.error, /did not expose recognizable message containers/);
}

async function testIdenticalTextOnlyTurnsAreMarkedAmbiguous() {
  const harness = createHarness("ambiguous-duplicate");
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.sequence_order_conflict, true);
  assert.equal(response.data.truncated, true,
    "identical text-only turns without stable provider IDs must not be silently deduplicated");
}

async function testProviderUsageLimitsTriggerSafeProviderRotationSignal() {
  const messages = [
    "You've reached your GPT-5 limit",
    "You have reached your daily limit",
    "Quota exceeded",
    "Limite de mensagens atingido",
    "Atingiste o limite diário"
  ];
  for (const message of messages) {
    const harness = createHarness("no-oldest-marker", "chatgpt", message);
    assert.equal(harness.getPageReadyMessage().blocked, "rate_limited", message);
  }
}

async function testScrollHardLimitIsExplicitlyTruncated() {
  const harness = createHarness("scroll-limit");
  const response = await harness.capture();
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.scroll_steps, 100);
  assert.equal(response.data.truncated, true);
  assert.equal(response.data.history_start_reached, false);
  assert.equal(response.data.oldest_boundary, "unknown");
}

async function main() {
  await testVirtualizedHistoryWindowsAndDuplicates();
  await testProviderScopedSelectorsRemainSupported();
  await testClaudeProjectConversationRouteUsesConversationId();
  await testClaudeNestedMessageWrappersAreNotDuplicated();
  await testClaudeNonConversationRoutesFailClosed();
  await testMissingOldestMarkerRemainsPartialOrUnknown();
  await testTopLoadingHardLimitIsExplicitlyTruncated();
  await testProviderDomMismatchFailsClosed();
  await testIdenticalTextOnlyTurnsAreMarkedAmbiguous();
  await testScrollHardLimitIsExplicitlyTruncated();
  await testProviderUsageLimitsTriggerSafeProviderRotationSignal();
  process.stdout.write("PASS: 11 deterministic virtualized-history, Claude route and provider-limit fixtures\n");
}

main().catch(error => {
  process.stderr.write((error && error.stack) || String(error));
  process.exitCode = 1;
});
