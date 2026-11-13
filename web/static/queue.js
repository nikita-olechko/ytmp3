const queue = [];
let running = false;

const list = document.getElementById("queue");
const form = document.getElementById("add");
const urlsInput = document.getElementById("urls");
const qualityInput = document.getElementById("quality");
const targetInput = document.getElementById("target");
const submitButton = document.getElementById("add-submit");
const TARGET_KEY = "ytmp3.target";
const targetListeners = [];

function currentTarget() {
  return targetInput ? targetInput.value : "device";
}

function applyTarget() {
  submitButton.textContent = currentTarget() === "library" ? "Add to library" : "Add & download";
  try { localStorage.setItem(TARGET_KEY, currentTarget()); } catch {}
  targetListeners.forEach((fn) => fn(currentTarget()));
}

if (targetInput) {
  try {
    const saved = localStorage.getItem(TARGET_KEY);
    if (saved) targetInput.value = saved;
  } catch {}
  targetInput.addEventListener("change", applyTarget);
  applyTarget();
}

function render(item) {
  item.el.className = item.state;
  item.el.querySelector(".status").textContent = item.message;
}

function enqueue(url, quality, label = url, target = currentTarget()) {
  const el = document.createElement("li");
  el.innerHTML = '<span class="url"></span><span class="status"></span>';
  el.querySelector(".url").textContent = label;
  list.prepend(el);
  const item = { url, quality, target, el, state: "pending", message: "Queued" };
  render(item);
  queue.push(item);
}

function saveBlob(blob, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

async function request(path, item) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: item.url, quality: item.quality }),
  });
  if (res.status === 401) {
    location.href = "/login";
    return null;
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return res;
}

async function toDevice(item) {
  const res = await request("/api/convert", item);
  if (!res) return null;
  const filename = decodeURIComponent(res.headers.get("X-Filename") || "audio.mp3");
  saveBlob(await res.blob(), filename);
  return filename;
}

async function toLibrary(item) {
  const res = await request("/api/library", item);
  if (!res) return null;
  const data = await res.json();
  return `Saved to library: ${data.saved}`;
}

async function convert(item) {
  item.state = "working";
  item.message = item.target === "library" ? "Converting and saving to library…" : "Converting…";
  render(item);
  try {
    const message = await (item.target === "library" ? toLibrary(item) : toDevice(item));
    if (message === null) return;
    item.state = "done";
    item.message = message;
  } catch (e) {
    item.state = "failed";
    item.message = e.message;
  }
  render(item);
}

async function drain() {
  if (running) return;
  running = true;
  while (queue.length) await convert(queue.shift());
  running = false;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  urlsInput.value
    .split(/\s+/)
    .map((u) => u.trim())
    .filter(Boolean)
    .forEach((u) => enqueue(u, qualityInput.value));
  urlsInput.value = "";
  drain();
});

window.ytQueue = {
  add(url, label) {
    enqueue(url, qualityInput.value, label);
    drain();
  },
  target: currentTarget,
  onTargetChange(fn) {
    targetListeners.push(fn);
  },
};
