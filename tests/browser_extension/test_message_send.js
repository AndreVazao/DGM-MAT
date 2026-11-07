"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "../../browser_extension/content.js"),
  "utf8"
);

let listener;
let responseCalled = false;
let sendClicks = 0;

const sandbox = {
  URL, Map, Set, Promise, Math, Date, Error, String, Array, Object, RegExp, Number, JSON,
  document: { title: "ChatGPT", body: { innerText: "" }, querySelectorAll() { return []; } },
  location: {
    href: "https://chatgpt.com/c/fixture-conversation",
    pathname: "/c/fixture-conversation",
    assign() { throw new Error("Unexpected navigation."); }
  },
  getComputedStyle() { return { display: "block", visibility: "visible" }; },
  chrome: {
    runtime: {
      onMessage: { addListener(callback) { listener = callback; } },
      sendMessage() { return Promise.resolve({ ok: true }); }
    }
  },
  setTimeout(callback) { callback(); return 1; }
};

vm.runInNewContext(source, sandbox, { filename: "browser_extension/content.js" });

const accepted = listener(
  { type: "DGM_SEND_MESSAGE", text: "This must not bypass the server approval queue." },
  {},
  () => { responseCalled = true; }
);

assert.equal(accepted, false, "direct send messages must not be handled by the content script");
assert.equal(responseCalled, false, "no direct-send result may be returned");
assert.equal(sendClicks, 0, "no provider UI action may occur through the unapproved message type");

process.stdout.write("PASS: direct content-script send bypass is rejected; approved task handler remains separate.\\n");
