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
    }
  };
  const document = {
    title: "Existing conversation | ChatGPT",
    body: { innerText: "" },
    querySelectorAll(selector) {
      if (selector === "[data-message-author-role]") return messages;
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
      href: "https://chatgpt.com/c/fixture-conversation",
      pathname: "/c/fixture-conversation",
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

  process.stdout.write("PASS: 4 visible-UI message-send safety fixtures\\n");
}

main().catch(error => {
  process.stderr.write((error && error.stack) || String(error));
  process.exitCode = 1;
});
