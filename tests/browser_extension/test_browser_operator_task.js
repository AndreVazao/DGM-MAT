"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "../../browser_extension/content.js"),
  "utf8"
);

class FakeTextArea {
  constructor() {
    this._value = "";
    this.disabled = false;
    this.isConnected = true;
    this.attributes = {};
    this.innerText = "";
    this.textContent = "";
  }
  get value() { return this._value; }
  set value(value) { this._value = value; }
  getBoundingClientRect() { return { width: 500, height: 80 }; }
  getAttribute(name) { return this.attributes[name] || null; }
  dispatchEvent() { return true; }
  focus() {}
  closest() { return null; }
}

class FakeMessage {
  constructor(role, text) {
    this.isConnected = true;
    this.innerText = text;
    this.textContent = text;
    this.tagName = "DIV";
    this.className = "";
    this.parentElement = null;
    this.attributes = {
      "data-message-author-role": role,
      "data-message-id": role + "-" + Math.random().toString(16).slice(2)
    };
  }
  getBoundingClientRect() { return { width: 500, height: 60 }; }
  getAttribute(name) { return this.attributes[name] || null; }
  querySelector() { return null; }
  contains() { return false; }
}

function createHarness(options = {}) {
  const messages = [];
  const composer = new FakeTextArea();
  let sendClicks = 0;
  let listener;
  let virtualNow = 1000;

  const sendButton = {
    disabled: false,
    getAttribute() { return null; },
    getBoundingClientRect() { return { width: 40, height: 40 }; },
    click() {
      sendClicks += 1;
      if (options.noUserEcho) return;
      messages.push(new FakeMessage("user", composer.value));
      if (!options.noAssistantResponse) {
        messages.push(new FakeMessage("assistant", options.assistantText || "Verified test response."));
      }
    }
  };

  const document = {
    title: "Existing conversation | ChatGPT",
    body: { innerText: options.blockedText || "" },
    querySelectorAll(selector) {
      if (selector === "[data-message-author-role]") return messages;
      if (selector === "#prompt-textarea" ||
          selector === '[data-testid="prompt-textarea"]' ||
          selector === "textarea[placeholder]" ||
          selector === "textarea") return [composer];
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
    RegExp, Number, JSON, document,
    location: {
      href: "https://chatgpt.com/c/fixture-conversation",
      pathname: "/c/fixture-conversation",
      assign() { throw new Error("Unexpected navigation."); }
    },
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
    setTimeout(callback, ms) {
      virtualNow += Number(ms) || 0;
      queueMicrotask(callback);
      return 1;
    }
  };

  vm.runInNewContext(source, sandbox, { filename: "browser_extension/content.js" });

  return {
    execute(request) {
      return new Promise(resolve => {
        const accepted = listener(
          { type: "DGM_EXECUTE_BROWSER_TASK", ...request },
          {},
          response => resolve(response)
        );
        assert.equal(accepted, true);
      });
    },
    sendClicks: () => sendClicks
  };
}

async function main() {
  const success = createHarness();
  const completed = await success.execute({
    provider: "chatgpt",
    source_id: "fixture-conversation",
    message: "Review the approved task and report concise findings.",
    response_timeout_ms: 5000
  });
  assert.equal(completed.ok, true, completed.error);
  assert.equal(completed.data.status, "completed");
  assert.equal(completed.data.sent_status, "submitted_and_visible");
  assert.equal(completed.data.verification, "assistant_response_observed_stable");
  assert.equal(completed.data.assistant_text, "Verified test response.");
  assert.equal(success.sendClicks(), 1);

  const wrongProvider = createHarness();
  const providerMismatch = await wrongProvider.execute({
    provider: "gemini",
    source_id: "fixture-conversation",
    message: "Must not send."
  });
  assert.equal(providerMismatch.ok, false);
  assert.match(providerMismatch.error, /provider does not match/i);
  assert.equal(wrongProvider.sendClicks(), 0);

  const wrongConversation = createHarness();
  const conversationMismatch = await wrongConversation.execute({
    provider: "chatgpt",
    source_id: "another-conversation",
    message: "Must not send."
  });
  assert.equal(conversationMismatch.ok, false);
  assert.match(conversationMismatch.error, /conversation does not match/i);
  assert.equal(wrongConversation.sendClicks(), 0);

  const blocked = createHarness({ blockedText: "Too many requests. Try again later." });
  const blockedResult = await blocked.execute({
    provider: "chatgpt",
    source_id: "fixture-conversation",
    message: "Must not send."
  });
  assert.equal(blockedResult.ok, true);
  assert.equal(blockedResult.data.status, "blocked");
  assert.equal(blockedResult.data.sent_status, "not_sent");
  assert.equal(blocked.sendClicks(), 0);

  const unverified = createHarness({ noUserEcho: true });
  const unverifiedResult = await unverified.execute({
    provider: "chatgpt",
    source_id: "fixture-conversation",
    message: "Do not automatically retry."
  });
  assert.equal(unverifiedResult.ok, true);
  assert.equal(unverifiedResult.data.status, "unverified");
  assert.equal(unverifiedResult.data.reason, "user_message_not_verified");
  assert.equal(unverified.sendClicks(), 1);

  const timeout = createHarness({ noAssistantResponse: true });
  const timeoutResult = await timeout.execute({
    provider: "chatgpt",
    source_id: "fixture-conversation",
    message: "Wait for an answer.",
    response_timeout_ms: 1000
  });
  assert.equal(timeoutResult.ok, true);
  assert.equal(timeoutResult.data.status, "unverified");
  assert.equal(timeoutResult.data.reason, "assistant_response_timeout");
  assert.equal(timeout.sendClicks(), 1);

  process.stdout.write("PASS: 5 browser operator content-task safety fixtures\\n");
}

main().catch(error => {
  process.stderr.write((error && error.stack) || String(error));
  process.exitCode = 1;
});
