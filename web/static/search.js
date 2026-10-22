const searchForm = document.getElementById("search");
const queryInput = document.getElementById("query");
const results = document.getElementById("results");
const meta = document.getElementById("search-meta");
const searchStatus = document.getElementById("search-status");
const copyListButton = document.getElementById("copy-list");

let lastResults = [];

function formatDuration(seconds) {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return m >= 60 ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

async function copyText(text, button) {
  await navigator.clipboard.writeText(text);
  const original = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => (button.textContent = original), 1200);
}

function renderResult(r) {
  const li = document.createElement("li");
  li.innerHTML = `
    <img loading="lazy" alt="">
    <div class="info">
      <a class="title" target="_blank" rel="noopener"></a>
      <span class="sub"></span>
    </div>
    <div class="actions">
      <button type="button" class="dl">Download</button>
      <button type="button" class="link copy">Copy link</button>
    </div>`;
  li.querySelector("img").src = r.thumbnail;
  const title = li.querySelector(".title");
  title.textContent = r.title;
  title.href = r.url;
  li.querySelector(".sub").textContent = [r.channel, formatDuration(r.duration)].filter(Boolean).join(" · ");
  li.querySelector(".dl").addEventListener("click", (e) => {
    window.ytQueue.add(r.url, r.title);
    e.target.textContent = "Queued";
    e.target.disabled = true;
  });
  li.querySelector(".copy").addEventListener("click", (e) => copyText(r.url, e.target));
  return li;
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = queryInput.value.trim();
  if (!q) return;
  meta.hidden = false;
  copyListButton.hidden = true;
  searchStatus.textContent = "Searching…";
  results.replaceChildren();
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=10`);
    if (res.status === 401) {
      location.href = "/login";
      return;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    lastResults = data.results;
    searchStatus.textContent = `${lastResults.length} results`;
    copyListButton.hidden = lastResults.length === 0;
    results.replaceChildren(...lastResults.map(renderResult));
  } catch (err) {
    searchStatus.textContent = err.message;
  }
});

copyListButton.addEventListener("click", () =>
  copyText(lastResults.map((r) => `${r.title} — ${r.url}`).join("\n"), copyListButton)
);
