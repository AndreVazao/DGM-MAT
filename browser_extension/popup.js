const pairInput = document.getElementById("pair-code");
const pairButton = document.getElementById("pair-button");
const startButton = document.getElementById("start-button");
const stopButton = document.getElementById("stop-button");
const statusNode = document.getElementById("status");

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

async function refresh() {
  try {
    const data = await send({ type: "DGM_GET_STATUS" });
    startButton.disabled = !data.paired || Boolean(data.run?.active);
    showStatus(data.last_status || (data.paired ? "Paired and ready." : "Pair with the local DGM-MAT PC."));
  } catch (error) {
    startButton.disabled = true;
    showStatus(error.message, true);
  }
}

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
