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
    this.innerText = "";
    this.textContent = "";
    this.attributes = {};
  }
  get value() { return this._value; }
  set value(value) { this._value = value; }
  getBoundingClientRect() { return { width: 500, height: 80 }; }
  getAttribute(name) { return this.attributes[name] || null; }
  dispatchEvent() { return true; }
  focus() {}
  closest() { return null; }
}

class FakeInputEvent {
  constructor(type, options) { this.type = type; this.options = options; }
}
class FakeEvent {
  constructor(type) { this.type = type; }
}

function createHarness(options = {}) {
  const provider = options.provider || "chatgpt";
  const messages = [];
  const composer = options.noComposer ? null : new FakeTextArea();
  let clicked = false;
  let listener;
  const sendButton = {
    disabled: false,
    getAttribute() { return null; },
    getBoundingClientRect() { return { width: 40, height: 40 }; },
    click() {
      clicked = true;
      if (options.noVisibleConfirmation) return;
      messages.push({
        isConnected: true,
        innerText: composer.value,
        id: "user-turn-1",
        tagName: "DIV",
        parentElement: null,
        getBoundingClientRect() { return { width: 500, height: 60 }; },
        getAttribute(name) {
          if (name === "data-message-author-role") return "user";
          if (name === "data-message-id") return "user-turn-1";
          return null;
        },
        querySelector() { return null; },
        contains() { return false; }
      });
      if (options.assistantResponse) {
        messages.push({
          isConnected: true,
          innerText: options.assistantResponse,
          id: "assistant-turn-1",
          tagName: "DIV",
          parentElement: null,
          getBoundingClientRect() { return { width: 500, height: 80 }; },
          getAttribute(name) {
            if (name === "data-message-author-role") return "assistant";
            if (name === "data-message-id") return "assistant-turn-1";
            return null;
          },
          querySelector() { return null; },
          contains() { return false; }
        });
      }
    }
  };
  const document = {
    title: "Existing conversation | " + provider,
    body: { innerText: options.bodyText || "" },
    querySelectorAll(selector) {
      if (selector === "[data-message-author-role]" || selector === "[data-message-id]" ||
          selector === '[data-testid="conversation-turn"]' || selector === '[data-testid*="message"]' ||
          selector.includes('div[class*=')) return messages;
      if (selector === "#prompt-textarea" || selector === '[data-testid="prompt-textarea"]' ||
          selector === "textarea[placeholder]" || selector === "textarea") {
        return composer ? [composer] : [];
      }
      if (selector.includes("button[")) return [sendButton];
      return [];
    },
    querySelector() { return null; }
  };
  const sandbox = {
    URL, Map, Set, Promise, Math, Date, Error, String, Array, Object, RegExp, Number, JSON,
    document,
    location: {
      href: {
        chatgpt: "https://chatgpt.com/c/fixture-conversation",
        deepseek: "https://chat.deepseek.com/a/chat/s/fixture-conversation",
        qwen: "https://chat.qwen.ai/chat/fixture-conversation"
      }[provider],
      pathname: {
        chatgpt: "/c/fixture-conversation",
        deepseek: "/a/chat/s/fixture-conversation",
        qwen: "/chat/fixture-conversation"
      }[provider],
      assign() { throw new Error("Unexpected navigation."); }
    },
    HTMLTextAreaElement: FakeTextArea,
    HTMLInputElement: class FakeInput {},
    InputEvent: FakeInputEvent,
    Event: FakeEvent,
    getComputedStyle() { return { display: "block", visibility: "visible", overflowY: "auto" }; },
    chrome: {
      runtime: {
        onMessage: { addListener(callback) { listener = callback; } },
        sendMessage() { return Promise.resolve({ ok: true }); }
      }
    },
    setTimeout(callback) { callback(); return 1; }
  };
  vm.runInNewContext(source, sandbox, { filename: "browser_extension/content.js" });
  return {
    send(request) {
      return new Promise(resolve => {
        const accepted = listener({ type: "DGM_SEND_MESSAGE", ...request }, {}, response => resolve(response));
        assert.equal(accepted, true);
      });
    },
    execute(request) {
      return new Promise(resolve => {
        const accepted = listener({ type: "DGM_EXECUTE_BROWSER_TASK", ...request }, {}, response => resolve(response));
        assert.equal(accepted, true);
      });
    },
    ping() {
      return new Promise(resolve => {
        const accepted = listener({ type: "DGM_PROVIDER_PING" }, {}, response => resolve(response));
        assert.equal(accepted, false);
      });
    },
    clicked: () => clicked
  };
}

async function main() {
  const success = createHarness();
  const response = await success.send({
    text: "Inspect the repository status and report verified findings.",
    source_id: "fixture-conversation"
  });
  assert.equal(response.ok, true, response.error);
  assert.equal(response.data.status, "submitted_and_visible");
  assert.equal(response.data.verification, "user_message_observed_in_conversation");
  assert.equal(success.clicked(), true);

  const mismatch = createHarness();
  const mismatchResponse = await mismatch.send({ text: "Do not send.", source_id: "different-conversation" });
  assert.equal(mismatchResponse.ok, false);
  assert.match(mismatchResponse.error, /conversation changed/);
  assert.equal(mismatch.clicked(), false);

  const noComposer = createHarness({ noComposer: true });
  const noComposerResponse = await noComposer.send({ text: "Do not send." });
  assert.equal(noComposerResponse.ok, false);
  assert.match(noComposerResponse.error, /composer/);
  assert.equal(noComposer.clicked(), false);

  const unverified = createHarness({ noVisibleConfirmation: true });
  const unverifiedResponse = await unverified.send({ text: "Single send only." });
  assert.equal(unverifiedResponse.ok, true);
  assert.equal(unverifiedResponse.data.status, "submitted_unverified");
  assert.equal(unverified.clicked(), true);

  for (const provider of ["chatgpt", "deepseek", "qwen"]) {
    const ping = await createHarness({ provider }).ping();
    assert.equal(ping.ok, true);
    assert.equal(ping.provider, provider);
  }

  const limited = createHarness({ bodyText: "You've reached your daily usage limit. Try again later." });
  const limitedResponse = await limited.execute({
    provider: "chatgpt",
    source_id: "fixture-conversation",
    message: "Do not send while this provider is limited.",
    response_timeout_ms: 1000
  });
  assert.equal(limitedResponse.ok, true, limitedResponse.error);
  assert.equal(limitedResponse.data.status, "blocked");
  assert.equal(limitedResponse.data.reason, "rate_limited");
  assert.equal(limited.clicked(), false, "a provider quota page must be detected before sending");

  for (const provider of ["deepseek", "qwen"]) {
    const providerHarness = createHarness({
      provider,
      assistantResponse: "The provider adapter returned a verified fixture response."
    });
    const providerResult = await providerHarness.execute({
      provider,
      source_id: "fixture-conversation",
      message: "Check this provider's visible composer and response.",
      response_timeout_ms: 1000
    });
    assert.equal(providerResult.ok, true, provider + ": " + providerResult.error);
    assert.equal(providerResult.data.status, "completed", provider);
    assert.match(providerResult.data.assistant_text, /verified fixture response/);
  }

  const mission = createHarness({ assistantResponse: "The repository is clean and the CI is green." });
  const missionResponse = await mission.execute({
    provider: "chatgpt",
    source_id: "fixture-conversation",
    message: "Inspect the repository and report.",
    response_timeout_ms: 1000
  });
  assert.equal(missionResponse.ok, true, missionResponse.error);
  assert.equal(missionResponse.data.status, "completed");
  assert.match(missionResponse.data.assistant_text, /repository is clean/);

  process.stdout.write("PASS: 9 visible-UI message, readiness, quota, five-provider and mission-response fixtures\\n");
}

main().catch(error => {
  process.stderr.write((error && error.stack) || String(error));
  process.exitCode = 1;
});
