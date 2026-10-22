const queue = [];
let running = false;

const list = document.getElementById("queue");
const form = document.getElementById("add");
const urlsInput = document.getElementById("urls");
const qualityInput = document.getElementById("quality");

function render(item) {
  item.el.className = item.state;
  item.el.querySelector(".status").textContent = item.message;
}

function enqueue(url, quality, label = url) {
  const el = document.createElement("li");
  el.innerHTML = '<span class="url"></span><span class="status"></span>';
  el.querySelector(".url").textContent = label;
  list.prepend(el);
  const item = { url, quality, el, state: "pending", message: "Queued" };
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

async function convert(item) {
  item.state = "working";
  item.message = "Converting…";
  render(item);
  try {
    const res = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: item.url, quality: item.quality }),
    });
    if (res.status === 401) {
      location.href = "/login";
      return;
    }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    const filename = decodeURIComponent(res.headers.get("X-Filename") || "audio.mp3");
    saveBlob(await res.blob(), filename);
    item.state = "done";
    item.message = filename;
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
};
