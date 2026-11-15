const assistantLog = document.getElementById("assistant-log");
const assistantForm = document.getElementById("assistant-form");
const assistantInput = document.getElementById("assistant-input");
const assistantSend = document.getElementById("assistant-send");
const assistantStatus = document.getElementById("assistant-status");
const POLL_MS = 4000;
const HIDDEN_POLL_MS = 30000;

let lastRendered = "";

/** Parsed JSON body, or an error naming the HTTP status when the server sent something else. */
async function readJson(res) {
  try {
    return await res.json();
  } catch {
    throw new Error(`Server error (${res.status})`);
  }
}
let pollTimer = null;

function nearBottom() {
  return assistantLog.scrollHeight - assistantLog.scrollTop - assistantLog.clientHeight < 40;
}

function renderMessages(messages) {
  const key = messages.map((m) => m.id).join(",") + (messages.at(-1)?.text.length || 0);
  if (key === lastRendered) return;
  lastRendered = key;
  const stick = nearBottom();
  assistantLog.replaceChildren(...messages.map((m) => {
    const line = document.createElement("div");
    line.className = `line ${m.role}`;
    line.textContent = m.role === "user" ? `> ${m.text}` : m.text;
    return line;
  }));
  if (!messages.length) assistantLog.textContent = "No conversation yet. Your first message starts a session.";
  if (stick) assistantLog.scrollTop = assistantLog.scrollHeight;
}

function describe(data) {
  if (!data.running) return "No session running; sending starts one";
  return data.status ? `Session: ${data.status}` : "Session running";
}

async function refresh() {
  try {
    const res = await fetch("/api/assistant/conversation");
    if (res.status === 401) return (location.href = "/login");
    const data = await readJson(res);
    if (!res.ok) throw new Error(data.error || "Could not load the conversation");
    renderMessages(data.messages || []);
    assistantStatus.textContent = describe(data);
  } catch (e) {
    assistantStatus.textContent = e.message;
  }
}

function schedule() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(async () => {
    await refresh();
    schedule();
  }, document.hidden ? HIDDEN_POLL_MS : POLL_MS);
}

assistantForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = assistantInput.value.trim();
  if (!message) return;
  assistantSend.disabled = true;
  assistantStatus.textContent = "Sending…";
  try {
    const res = await fetch("/api/assistant/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await readJson(res);
    if (!res.ok || data.ok === false) throw new Error(data.error || data.message || "Sending failed");
    assistantInput.value = "";
    assistantStatus.textContent = data.message;
    setTimeout(refresh, 1500);
  } catch (e) {
    assistantStatus.textContent = e.message;
  } finally {
    assistantSend.disabled = false;
  }
});

assistantInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    assistantForm.requestSubmit();
  }
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refresh();
  schedule();
});

refresh();
schedule();
