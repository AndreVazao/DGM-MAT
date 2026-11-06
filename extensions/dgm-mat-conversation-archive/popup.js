const PROVIDERS = [
  { provider: "chatgpt", hosts: ["chatgpt.com", "chat.openai.com"], conversation: /\/(c|share)\/[a-z0-9-]+/i },
  { provider: "grok", hosts: ["grok.com"], conversation: /\/(chat|c)\/[^/?#]+/i },
  { provider: "gemini", hosts: ["gemini.google.com"], conversation: /\/app\/[^/?#]+/i },
  { provider: "claude", hosts: ["claude.ai"], conversation: /\/(chat|project)\/[^/?#]+/i }
];

const statusNode = document.getElementById("status");
const inventoryButton = document.getElementById("inventory");
const captureButton = document.getElementById("capture");

function providerForUrl(value) {
  try {
    const url = new URL(value);
    return PROVIDERS.find(item => item.hosts.includes(url.hostname.toLowerCase())) || null;
  } catch { return null; }
}

function isConversationUrl(provider, value) {
  try { return provider.conversation.test(new URL(value).pathname); }
  catch { return false; }
}

async function stableId(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).slice(0, 12)
    .map(byte => byte.toString(16).padStart(2, "0")).join("");
}

function setBusy(busy, message) {
  inventoryButton.disabled = busy;
  captureButton.disabled = busy;
  statusNode.textContent = message;
}

async function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  try {
    return await chrome.downloads.download({
      url: objectUrl,
      filename: "DGM-MAT-Conversation-Archive/" + filename,
      saveAs: false,
      conflictAction: "uniquify"
    });
  } finally {
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
  }
}

async function inventoryHistory() {
  setBusy(true, "A consultar apenas o histórico dos domínios das IAs…");
  try {
    const found = new Map();
    for (const provider of PROVIDERS) {
      for (const host of provider.hosts) {
        const entries = await chrome.history.search({ text: host, startTime: 0, maxResults: 10000 });
        for (const entry of entries) {
          const detected = providerForUrl(entry.url);
          if (!detected || detected.provider !== provider.provider || !isConversationUrl(provider, entry.url)) continue;
          const id = await stableId(entry.url);
          found.set(entry.url, {
            id: provider.provider + "-" + id,
            provider: provider.provider,
            title: entry.title || "Conversa sem título",
            url: entry.url,
            last_visit_at: entry.lastVisitTime ? new Date(entry.lastVisitTime).toISOString() : null,
            visit_count: entry.visitCount || 0,
            capture_status: "discovered",
            messages_captured: false,
            source: "chrome_history"
          });
        }
      }
    }
    const items = Array.from(found.values()).sort((a, b) =>
      String(b.last_visit_at || "").localeCompare(String(a.last_visit_at || ""))
    );
    const providerCounts = Object.fromEntries(PROVIDERS.map(p => [
      p.provider, items.filter(item => item.provider === p.provider).length
    ]));
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const payload = {
      schema: "dgm-mat.chrome-conversation-inventory.v1",
      generated_at: new Date().toISOString(),
      source: "chrome_history",
      coverage: "partial_browser_history_only",
      discovered_count: items.length,
      provider_counts: providerCounts,
      messages_captured: false,
      items,
      limitations: [
        "Este inventário contém apenas URLs de conversas presentes no histórico local do Chrome.",
        "Não prova que todas as conversas existentes na conta do provider foram descobertas.",
        "Não lê cookies, palavras-passe, tokens, localStorage ou dados de autenticação."
      ]
    };
    await downloadJson("inventory-" + stamp + ".json", payload);
    statusNode.textContent = "Inventário concluído: " + items.length + " conversas encontradas.\n" +
      PROVIDERS.map(p => p.provider + ": " + providerCounts[p.provider]).join("\n") +
      "\nFicheiro guardado nas transferências.";
  } catch (error) {
    statusNode.textContent = "Falha no inventário: " + String(error?.message || error);
  } finally {
    setBusy(false, statusNode.textContent);
  }
}

function extractVisibleConversation(providerName) {
  const main = document.querySelector("main") || document.body;
  const selectors = {
    chatgpt: "[data-message-author-role]",
    claude: '[data-testid="user-message"], [data-testid="assistant-message"], [data-testid="chat-message"]',
    gemini: "user-query, model-response, [data-test-id='user-query'], [data-test-id='model-response']",
    grok: '[data-testid="message"], [data-testid^="message-"]'
  };
  const selector = selectors[providerName] || "";
  const nodes = selector ? Array.from(main.querySelectorAll(selector)) : [];
  const messages = [];
  const seen = new Set();

  for (const node of nodes) {
    const content = (node.innerText || node.textContent || "").trim();
    if (!content) continue;
    const testId = node.getAttribute("data-testid") || "";
    const tag = node.tagName.toLowerCase();
    const roleAttr = (node.getAttribute("data-message-author-role") ||
      node.getAttribute("data-author") || node.getAttribute("data-role") || "").toLowerCase();
    let role = roleAttr;
    if (!role) {
      if (tag === "user-query" || /user/.test(testId)) role = "user";
      else if (tag === "model-response" || /assistant|model/.test(testId)) role = "assistant";
      else role = "unknown";
    }
    if (role.includes("assistant") || role.includes("model")) role = "assistant";
    if (role.includes("user")) role = "user";
    const id = node.getAttribute("data-message-id") || node.id || testId || providerName + "-message-" + messages.length;
    const fingerprint = role + "|" + content;
    if (seen.has(fingerprint)) continue;
    seen.add(fingerprint);
    messages.push({
      id, role, content, sequence: messages.length, timestamp: null,
      metadata: { selector, tag, test_id: testId || null }
    });
  }

  const fallbackContent = (main.innerText || "").trim();
  return {
    url: location.href,
    title: document.title,
    provider: providerName,
    captured_at: new Date().toISOString(),
    content: messages.length
      ? messages.map(message => message.role + ": " + message.content).join("\n\n")
      : fallbackContent,
    messages,
    completeness: messages.length ? "partial_dom_snapshot" : "partial_page_text_only",
    metadata: {
      extraction_method: "provider_dom_selectors_v1",
      selector,
      candidate_nodes: nodes.length,
      message_count: messages.length,
      fallback_text_used: messages.length === 0,
      capture_scope: "currently_loaded_dom_nodes_only",
      complete_history_verified: false,
      document_ready_state: document.readyState
    }
  };
}

async function captureCurrentConversation() {
  setBusy(true, "A verificar a conversa atualmente aberta…");
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url) throw new Error("Não existe um separador ativo acessível.");
    const provider = providerForUrl(tab.url);
    if (!provider) throw new Error("O separador ativo não pertence a ChatGPT, Grok, Gemini ou Claude.");
    if (!isConversationUrl(provider, tab.url)) throw new Error("Abre primeiro uma conversa individual, não apenas a página inicial da IA.");

    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id }, func: extractVisibleConversation, args: [provider.provider]
    });
    const captured = result?.result;
    if (!captured) throw new Error("Não foi possível ler o conteúdo visível da conversa.");
    const id = await stableId(captured.url);
    const payload = {
      schema: "dgm-mat.chrome-conversation-capture.v1",
      generated_at: new Date().toISOString(),
      source: "chrome_extension_dom",
      conversations: [{
        id: provider.provider + "-" + id,
        conversation_id: provider.provider + "-" + id,
        provider: provider.provider,
        title: captured.title || "Conversa sem título",
        url: captured.url,
        content: captured.content || "",
        messages: captured.messages || [],
        completeness: captured.completeness,
        captured_at: captured.captured_at,
        metadata: captured.metadata
      }]
    };
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    await downloadJson("capture-" + provider.provider + "-" + id + "-" + stamp + ".json", payload);
    statusNode.textContent = "Captura guardada: " + provider.provider + "\n" +
      "Mensagens reconhecidas: " + (captured.messages?.length || 0) + "\n" +
      "Completude: " + captured.completeness + "\n" +
      (captured.messages?.length ? "Mensagens com papéis identificados." : "Texto parcial: os papéis não foram inferidos.");
  } catch (error) {
    statusNode.textContent = "Falha na captura: " + String(error?.message || error);
  } finally {
    setBusy(false, statusNode.textContent);
  }
}

inventoryButton.addEventListener("click", inventoryHistory);
captureButton.addEventListener("click", captureCurrentConversation);
