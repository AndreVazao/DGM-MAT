const pairInput = document.getElementById("pair-code");
const pairButton = document.getElementById("pair-button");
const startButton = document.getElementById("start-button");
const stopButton = document.getElementById("stop-button");
const retryButton = document.getElementById("retry-button");
const autoCheckbox = document.getElementById("auto-checkbox");
const statusNode = document.getElementById("status");
const browserOperatorCheckbox = document.getElementById("browser-operator-checkbox");
const consultCheckbox = document.getElementById("consult-checkbox");
const consultStatus = document.getElementById("consult-status");
const consultForm = document.getElementById("consult-request-form");
const consultGoal = document.getElementById("consult-goal");
const consultMissionId = document.getElementById("consult-mission-id");
const consultLoadMissionButton = document.getElementById("consult-load-mission-button");
const consultContext = document.getElementById("consult-context");
const consultFreeConfirm = document.getElementById("consult-free-confirm");
const consultPreviewButton = document.getElementById("consult-preview-button");
const consultPreview = document.getElementById("consult-preview");
const consultPreviewStatus = document.getElementById("consult-preview-status");
const consultSubmit = document.getElementById("consult-submit");
let consultPreviewDigest = null;
let consultPreviewSnapshot = null;
const consultQueue = document.getElementById("consult-queue");

function showStatus(value, error = false) {
  statusNode.textContent = value;
  statusNode.style.color = error ? "#dc2626" : "";
}

function send(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, response => {
      const error = chrome.runtime.lastError;
      if (error) return reject(new Error(error.message));
      if (!response?.ok) return reject(new Error(response?.error || "DGM-MAT request failed."));
      resolve(response.data);
    });
  });
}

async function refreshConsultQueue() {
  try {
    const data = await send({ type: "DGM_LIST_BROWSER_CONSULTS" });
    const recent = Array.isArray(data.recent) ? data.recent : [];
    consultQueue.replaceChildren();
    if (!recent.length) {
      consultQueue.textContent = "Ainda não existem consultas.";
      return;
    }
    for (const item of recent) {
      const row = document.createElement("div");
      row.className = "consult-item";
      const label = document.createElement("span");
      label.textContent = item.provider + " · " + item.status + " · " + item.consultation_id.slice(-8);
      row.appendChild(label);
      if (item.status === "PENDING_APPROVAL") {
        const approve = document.createElement("button");
        approve.type = "button";
        approve.className = "secondary";
        approve.textContent = "Aprovar envio";
        approve.addEventListener("click", async () => {
          approve.disabled = true;
          try {
            await send({ type: "DGM_APPROVE_BROWSER_CONSULT", consultationId: item.consultation_id });
            await refreshConsultQueue();
            consultStatus.textContent = "Consulta aprovada; será enviada quando o separador autenticado estiver pronto.";
          } catch (error) {
            approve.disabled = false;
            showStatus(error.message, true);
          }
        });
        row.appendChild(approve);
      }
      consultQueue.appendChild(row);
    }
  } catch (error) {
    consultQueue.textContent = error.message;
  }
}

async function refresh() {
  try {
    const data = await send({ type: "DGM_GET_STATUS" });
    startButton.disabled = !data.paired || Boolean(data.run?.active);
    retryButton.disabled = !data.can_retry;
    autoCheckbox.checked = Boolean(data.auto_enabled);
    browserOperatorCheckbox.checked = Boolean(data.browser_operator_auto_enabled);
    consultCheckbox.checked = Boolean(data.browser_consult_enabled);
    consultStatus.textContent = data.browser_consult_status || "AI consultation idle.";
    await refreshConsultQueue();
    showStatus((data.last_status || (data.paired ? "Paired and ready." : "Pair with the local DGM-MAT PC.")) + "\n" + (data.browser_operator_status || "Browser mission operator idle."));
  } catch (error) {
    startButton.disabled = true;
    showStatus(error.message, true);
  }
}

function invalidateConsultPreview() {
  consultPreviewDigest = null;
  consultPreviewSnapshot = null;
  consultPreview.value = "";
  consultPreviewStatus.textContent = "Pedido alterado. Faz uma nova pré-visualização antes de colocar na fila.";
  consultSubmit.disabled = true;
}

function currentConsultDraft() {
  return {
    mission_id: consultMissionId.value.trim(),
    goal: consultGoal.value.trim(),
    context: consultContext.value.trim()
  };
}

consultMissionId.addEventListener("input", invalidateConsultPreview);
consultGoal.addEventListener("input", invalidateConsultPreview);
consultContext.addEventListener("input", invalidateConsultPreview);

consultLoadMissionButton.addEventListener("click", async () => {
  const missionId = consultMissionId.value.trim();
  if (!/^mission_[0-9a-f]{8}$/.test(missionId)) {
    return showStatus("Indica um ID de missão válido (mission_ seguido de 8 caracteres hexadecimais).", true);
  }
  consultLoadMissionButton.disabled = true;
  try {
    const result = await send({
      type: "DGM_LOAD_MISSION_CONSULT_CONTEXT",
      payload: { mission_id: missionId }
    });
    consultGoal.value = result.goal;
    consultContext.value = result.context;
    invalidateConsultPreview();
    consultPreviewStatus.textContent = "Contexto da missão carregado (" + result.mission_status + "). Revê e edita os campos; depois pré-visualiza o prompt exato.";
    showStatus("Contexto da missão carregado. Nenhuma IA foi contactada.");
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    consultLoadMissionButton.disabled = false;
  }
});

consultPreviewButton.addEventListener("click", async () => {
  const draft = currentConsultDraft();
  if (!draft.goal) return showStatus("Escreve o pedido antes de pré-visualizar.", true);
  consultPreviewButton.disabled = true;
  consultSubmit.disabled = true;
  try {
    const result = await send({ type: "DGM_PREVIEW_BROWSER_CONSULT", payload: draft });
    consultPreview.value = result.prompt;
    consultPreviewDigest = result.prompt_sha256;
    consultPreviewSnapshot = JSON.stringify(draft);
    consultPreviewStatus.textContent = "Pré-visualização pronta · SHA-256 " + result.prompt_sha256 + (result.prompt_redacted ? " · segredos removidos" : " · sem padrões de segredo detetados");
    consultSubmit.disabled = false;
  } catch (error) {
    invalidateConsultPreview();
    showStatus(error.message, true);
  } finally {
    consultPreviewButton.disabled = false;
  }
});

consultForm.addEventListener("submit", async event => {
  event.preventDefault();
  const draft = currentConsultDraft();
  if (!consultPreviewDigest || consultPreviewSnapshot !== JSON.stringify(draft)) return showStatus("Pré-visualiza novamente o texto exato antes de criar a consulta.", true);
  const providers = Array.from(consultForm.querySelectorAll('input[name="consult-provider"]:checked')).map(input => input.value);
  if (!providers.length) return showStatus("Seleciona pelo menos um fornecedor.", true);
  if (!consultFreeConfirm.checked) return showStatus("Confirma que as contas selecionadas são gratuitas.", true);
  const submit = document.getElementById("consult-submit");
  submit.disabled = true;
  try {
    const result = await send({
      type: "DGM_ENQUEUE_BROWSER_CONSULT",
      payload: {
        task_ref: /^mission_[0-9a-f]{8}$/.test(consultMissionId.value.trim())
          ? consultMissionId.value.trim()
          : "manual_" + Date.now(),
        goal: consultGoal.value.trim(),
        context: consultContext.value.trim(),
        providers,
        free_capacity_confirmed: true,
        preview_sha256: consultPreviewDigest
      }
    });
    consultMissionId.value = "";
    consultGoal.value = "";
    consultContext.value = "";
    consultFreeConfirm.checked = false;
    invalidateConsultPreview();
    consultStatus.textContent = result.consultation_ids.length + " consulta(s) criada(s), pendente(s) de aprovação.";
    await refreshConsultQueue();
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    submit.disabled = false;
  }
});

consultCheckbox.addEventListener("change", async () => {
  consultCheckbox.disabled = true;
  try {
    const result = await send({ type: "DGM_SET_AUTO_BROWSER_CONSULT", enabled: consultCheckbox.checked });
    consultStatus.textContent = result.enabled
      ? "Consulta ativa. Só são enviados pedidos aprovados no DGM-MAT."
      : "Consulta desativada.";
  } catch (error) {
    showStatus(error.message, true);
    await refresh();
  } finally {
    consultCheckbox.disabled = false;
  }
});

browserOperatorCheckbox.addEventListener("change", async () => {
  browserOperatorCheckbox.disabled = true;
  try {
    const result = await send({ type: "DGM_SET_AUTO_BROWSER_OPERATOR", enabled: browserOperatorCheckbox.checked });
    showStatus(result.enabled
      ? "Execução automática de tarefas aprovadas ativada."
      : "Execução automática de tarefas aprovadas desativada.");
  } catch (error) {
    showStatus(error.message, true);
    await refresh();
  } finally {
    browserOperatorCheckbox.disabled = false;
  }
});

autoCheckbox.addEventListener("change", async () => {
  autoCheckbox.disabled = true;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const result = await send({
      type: "DGM_SET_AUTO_RECOVERY",
      enabled: autoCheckbox.checked,
      tabId: Number.isInteger(tab?.id) ? tab.id : null
    });
    showStatus(result.enabled
      ? (result.started ? "Unattended recovery enabled and started." : "Unattended recovery enabled; it starts when an authenticated provider tab opens.")
      : "Unattended recovery disabled.");
  } catch (error) {
    showStatus(error.message, true);
    await refresh();
  } finally {
    autoCheckbox.disabled = false;
  }
});


pairButton.addEventListener("click", async () => {
  pairButton.disabled = true;
  try {
    const code = pairInput.value.trim();
    if (!code) throw new Error("Enter the one-time pairing code.");
    const result = await send({ type: "DGM_PAIR", code });
    pairInput.value = "";
    showStatus("Paired. Session expires at " + new Date(result.expires_at).toLocaleTimeString() + ".");
    await refresh();
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    pairButton.disabled = false;
  }
});

startButton.addEventListener("click", async () => {
  startButton.disabled = true;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !Number.isInteger(tab.id)) throw new Error("No active provider tab.");
    const result = await send({ type: "DGM_START_RECOVERY", tabId: tab.id });
    showStatus(result.finished ? "No pending conversations." : "Recovery started: " + result.next.title);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    await refresh();
  }
});

retryButton.addEventListener("click", async () => {
  retryButton.disabled = true;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !Number.isInteger(tab.id)) throw new Error("Open the provider tab to retry first.");
    const result = await send({ type: "DGM_RETRY_CURRENT", tabId: tab.id });
    showStatus(result.finished ? "No more pending conversations." : "Retry started: " + result.next.title);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    await refresh();
  }
});

stopButton.addEventListener("click", async () => {
  try {
    await send({ type: "DGM_STOP_RECOVERY" });
    showStatus("Recovery stopped by operator.");
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    await refresh();
  }
});

refresh();
