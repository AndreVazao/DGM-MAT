"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "../../browser_extension/content.js"),
  "utf8"
);

const PROVIDERS = {
  chatgpt: { blank: "https://chatgpt.com/", created: "https://chatgpt.com/c/new-chat-123" },
  gemini: { blank: "https://gemini.google.com/app", created: "https://gemini.google.com/app/new-chat-123" },
  grok: { blank: "https://grok.com/", created: "https://grok.com/chat/new-chat-123" },
  deepseek: { blank: "https://chat.deepseek.com/", created: "https://chat.deepseek.com/a/chat/s/new-chat-123" },
  qwen: { blank: "https://chat.qwen.ai/", created: "https://chat.qwen.ai/chat/new-chat-123" }
};

class FakeTextArea {
  constructor() {
    this.value = "";
    this.disabled = false;
    this.isConnected = true;
    this.innerText = "";
    this.textContent = "";
  }
  getBoundingClientRect() { return { width: 500, height: 80 }; }
  getAttribute() { return null; }
  dispatchEvent() { return true; }
  focus() {}
  closest() { return null; }
}

class FakeMessage {
  constructor(provider, role, text) {
    this.tagName = provider === "gemini"
      ? (role === "user" ? "USER-QUERY" : "MODEL-RESPONSE")
      : "DIV";
    this.isConnected = true;
    this.innerText = text;
    this.textContent = text;
    this.className = "";
    this.parentElement = null;
    this.attributes = provider === "chatgpt"
      ? { "data-message-author-role": role }
      : { "data-role": role };
  }
  getBoundingClientRect() { return { width: 500, height: 50 }; }
  getAttribute(name) { return this.attributes[name] || null; }
  contains() { return false; }
}

function createHarness(provider, options = {}) {
  const messages = options.priorMessages ? [
    new FakeMessage(provider, "user", "Old conversation content")
  ] : [];
  const composer = options.noComposer ? null : new FakeTextArea();
  let listener;
  let sendClicks = 0;
  let virtualNow = 1000;
  const location = {
    href: options.existingConversation ? PROVIDERS[provider].created : PROVIDERS[provider].blank,
    get pathname() { return new URL(this.href).pathname; },
    assign() { throw new Error("Unexpected navigation."); }
  };

  const sendButton = {
    disabled: false,
    getAttribute() { return null; },
    getBoundingClientRect() { return { width: 40, height: 40 }; },
    click() {
      sendClicks++;
      if (options.noNewConversationId) {
        messages.push(new FakeMessage(provider, "user", composer.value));
      } else {
        location.href = PROVIDERS[provider].created;
        messages.push(new FakeMessage(provider, "user", composer.value));
      }
      if (!options.noAssistantResponse) {
        messages.push(new FakeMessage(provider, "assistant", "Independent fixture response."));
      }
    }
  };

  const document = {
    title: "New chat",
    body: { innerText: options.blockedText || "" },
    querySelectorAll(selector) {
      if (provider === "chatgpt" && selector === "[data-message-author-role]") return messages;
      if (provider === "gemini" && selector === "user-query, model-response") return messages;
      if (provider === "grok" && [
        '[data-testid="conversation-turn"]', '[data-testid*="message"]', '[data-message-id]'
      ].includes(selector)) return messages;
      if (provider === "deepseek" && [
        '[data-message-id]', '[data-testid*="message"]', 'div[class*="ds-message"]', 'div[class*="message"]'
      ].includes(selector)) return messages;
      if (provider === "qwen" && [
        '[data-message-id]', '[data-testid*="message"]', 'div[class*="chat-message"]',
        'div[class*="message-item"]', 'div[class*="message"]'
      ].includes(selector)) return messages;
      if (composer && (selector.includes("textarea") || selector.includes("contenteditable") ||
          selector === "#prompt-textarea" || selector.includes("rich-textarea"))) return [composer];
      if (selector.startsWith("button[")) return [sendButton];
      return [];
    },
    querySelector() { return null; }
  };

  class FakeDate extends Date {
    static now() { return virtualNow; }
  }

  const sandbox = {
    URL, Map, Set, Promise, Math, Date: FakeDate, Error, String, Array, Object,
    RegExp, Number, JSON, document, location,
    HTMLTextAreaElement: FakeTextArea,
    HTMLInputElement: class FakeInput {},
    InputEvent: class FakeInputEvent { constructor(type, init) { this.type = type; this.init = init; } },
    Event: class FakeEvent { constructor(type) { this.type = type; } },
    getComputedStyle() { return { display: "block", visibility: "visible", overflowY: "auto" }; },
    chrome: {
      runtime: {
        onMessage: { addListener(callback) { listener = callback; } },
        sendMessage() { return Promise.resolve({ ok: true }); }
      }
    },
    setTimeout(callback, milliseconds) {
      virtualNow += Number(milliseconds) || 0;
      queueMicrotask(callback);
      return 1;
    }
  };

  vm.runInNewContext(source, sandbox, { filename: "browser_extension/content.js" });

  function ping() {
    return new Promise(resolve => {
      const accepted = listener({ type: "DGM_FRESH_REVIEW_PING" }, {}, resolve);
      assert.equal(accepted, false);
    });
  }

  function execute(request) {
    return new Promise(resolve => {
      const accepted = listener(
        { type: "DGM_EXECUTE_FRESH_REVIEW", ...request },
        {},
        resolve
      );
      assert.equal(accepted, true);
    });
  }

  return { ping, execute, sendClicks: () => sendClicks };
}

async function testFreshBlankPageProtocolAcrossAllProviders() {
  for (const provider of Object.keys(PROVIDERS)) {
    const harness = createHarness(provider);
    const preflight = await harness.ping();
    assert.equal(preflight.ok, true, provider + ": " + preflight.reason);
    assert.equal(preflight.fresh_review_ready, true);
    assert.equal(preflight.provider, provider);
    assert.equal(preflight.initial_source_id, null);
    assert.equal(preflight.initial_visible_message_count, 0);
    assert.equal(preflight.independence_attested, false);

    const result = await harness.execute({
      provider,
      preflight_nonce: preflight.preflight_nonce,
      message: "Review this bounded design brief without tools or prior context.",
      response_timeout_ms: 12000
    });
    assert.equal(result.ok, true, provider + ": " + result.error);
    assert.equal(result.data.status, "completed", provider);
    assert.equal(result.data.fresh_context_observed, true, provider);
    assert.equal(result.data.initial_source_id, null, provider);
    assert.equal(result.data.independence_attested, false, provider);
    assert.equal(result.data.source_id, "new-chat-123", provider);
    assert.equal(harness.sendClicks(), 1, provider);
  }
}

async function testExistingConversationIsRejectedBeforeSending() {
  const harness = createHarness("chatgpt", { existingConversation: true });
  const preflight = await harness.ping();
  assert.equal(preflight.ok, false);
  assert.equal(preflight.reason, "existing_conversation_detected");
  assert.equal(harness.sendClicks(), 0);
}

async function testVisiblePriorMessagesAreRejectedBeforeSending() {
  const harness = createHarness("gemini", { priorMessages: true });
  const preflight = await harness.ping();
  assert.equal(preflight.ok, false);
  assert.equal(preflight.reason, "visible_prior_messages_detected");
  assert.equal(harness.sendClicks(), 0);
}

async function testMissingComposerIsRejectedBeforeSending() {
  const harness = createHarness("qwen", { noComposer: true });
  const preflight = await harness.ping();
  assert.equal(preflight.ok, false);
  assert.equal(preflight.reason, "visible_composer_not_found");
  assert.equal(harness.sendClicks(), 0);
}

async function testPreflightNonceIsOneShotAndRequired() {
  const harness = createHarness("chatgpt");
  const preflight = await harness.ping();
  const bad = await harness.execute({
    provider: "chatgpt",
    preflight_nonce: "wrong",
    message: "Must not send."
  });
  assert.equal(bad.ok, false);
  assert.match(bad.error, /preflight is missing/i);
  assert.equal(harness.sendClicks(), 0);
  const retry = await harness.execute({
    provider: "chatgpt",
    preflight_nonce: preflight.preflight_nonce,
    message: "Must not send after failed one-shot."
  });
  assert.equal(retry.ok, false);
  assert.equal(harness.sendClicks(), 0);
}

async function testNoNewConversationIdIsUnverified() {
  const harness = createHarness("chatgpt", { noNewConversationId: true });
  const preflight = await harness.ping();
  const result = await harness.execute({
    provider: "chatgpt",
    preflight_nonce: preflight.preflight_nonce,
    message: "Must create a new provider conversation.",
    response_timeout_ms: 1000
  });
  assert.equal(result.ok, true);
  assert.equal(result.data.status, "unverified");
  assert.equal(result.data.reason, "new_conversation_not_observed");
  assert.equal(result.data.independence_attested, false);
}

async function main() {
  await testFreshBlankPageProtocolAcrossAllProviders();
  await testExistingConversationIsRejectedBeforeSending();
  await testVisiblePriorMessagesAreRejectedBeforeSending();
  await testMissingComposerIsRejectedBeforeSending();
  await testPreflightNonceIsOneShotAndRequired();
  await testNoNewConversationIdIsUnverified();
  process.stdout.write("PASS: fresh browser review preflight fixtures across five providers\\n");
}

main().catch(error => {
  process.stderr.write((error && error.stack) || String(error));
  process.exitCode = 1;
});
