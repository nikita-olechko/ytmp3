const features = window.discoverFeatures;
const seedForm = document.getElementById("seed");
const artistInput = document.getElementById("seed-artist");
const titleInput = document.getElementById("seed-title");
const seedStatus = document.getElementById("seed-status");
const similarList = document.getElementById("similar");
const hideOwned = document.getElementById("hide-owned");
const playingButton = document.getElementById("playing");

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    location.href = "/login";
    throw new Error("Not logged in");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Server error (HTTP ${res.status}), try again`);
  return data;
}

function actionButton(label, run) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", async () => {
    const row = button.closest("li");
    const status = row.querySelector(".status");
    row.querySelectorAll("button").forEach((b) => (b.disabled = true));
    status.textContent = `${label}…`;
    status.className = "status";
    try {
      status.textContent = await run();
      status.classList.add("ok");
    } catch (e) {
      status.textContent = e.message;
      status.classList.add("bad");
      row.querySelectorAll("button").forEach((b) => (b.disabled = false));
    }
  });
  return button;
}

function trackRow(title, sub, image, buttons) {
  const li = document.createElement("li");
  li.innerHTML = `<img alt="" loading="lazy"><div class="info"><span class="title"></span><span class="sub"></span><span class="status"></span></div><div class="actions"></div>`;
  li.querySelector(".title").textContent = title;
  li.querySelector(".sub").textContent = sub;
  const img = li.querySelector("img");
  if (image) img.src = image;
  else img.remove();
  li.querySelector(".actions").append(...buttons);
  return li;
}

function similarRow(t) {
  const buttons = [];
  if (features.songs) {
    buttons.push(actionButton("Get song", async () => {
      const r = await api("/api/discover/song", { artist: t.artist, title: t.title, duration: t.duration });
      return `Saved ${r.saved}`;
    }));
  }
  if (features.lidarr) {
    buttons.push(actionButton("Get album", async () => {
      const r = await api("/api/discover/album", { artist: t.artist, title: t.title });
      return `${r.album}: ${r.status}`;
    }));
  }
  const more = document.createElement("button");
  more.type = "button";
  more.className = "link";
  more.textContent = "More like this";
  more.addEventListener("click", () => {
    artistInput.value = t.artist;
    titleInput.value = t.title;
    findSimilar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  buttons.push(more);
  const owned = t.in_library ? " · in library" : "";
  const li = trackRow(t.title, `${t.artist} · ${Math.round(t.match * 100)}% match${owned}`, t.image, buttons);
  li.dataset.owned = t.in_library ? "1" : "";
  return li;
}

function applyFilter() {
  similarList.querySelectorAll("li").forEach((li) => (li.hidden = hideOwned.checked && li.dataset.owned === "1"));
}

async function findSimilar() {
  const artist = artistInput.value.trim();
  if (!artist) return;
  seedStatus.textContent = "Looking up similar songs…";
  similarList.replaceChildren();
  try {
    const params = new URLSearchParams({ artist, title: titleInput.value.trim() });
    const data = await api(`/api/discover/similar?${params}`);
    const owned = data.tracks.filter((t) => t.in_library).length;
    seedStatus.textContent = `${data.tracks.length} ${data.source}, ${owned} already in the library`;
    similarList.replaceChildren(...data.tracks.map(similarRow));
    applyFilter();
  } catch (e) {
    seedStatus.textContent = e.message;
  }
}

seedForm.addEventListener("submit", (e) => {
  e.preventDefault();
  findSimilar();
});
hideOwned.addEventListener("change", applyFilter);

if (playingButton) {
  playingButton.addEventListener("click", async () => {
    seedStatus.textContent = "Checking Navidrome…";
    try {
      const { playing } = await api("/api/discover/now-playing");
      if (!playing.length) {
        seedStatus.textContent = "Nothing is playing right now";
        return;
      }
      const latest = playing.reduce((a, b) => (b.minutes_ago < a.minutes_ago ? b : a));
      artistInput.value = latest.artist;
      titleInput.value = latest.title;
      findSimilar();
    } catch (e) {
      seedStatus.textContent = e.message;
    }
  });
}

const weeklyList = document.getElementById("weekly-list");
const weeklyStatus = document.getElementById("weekly-status");

async function loadWeekly() {
  try {
    const { tracks } = await api("/api/discover/weekly");
    weeklyStatus.textContent = tracks.length ? `${tracks.length} songs` : "Nothing downloaded yet";
    weeklyList.replaceChildren(...tracks.map((t) => trackRow(t.name, t.playlist, "", [
      actionButton("Keep", async () => `Kept as ${(await api("/api/discover/weekly/keep", { path: t.path })).kept}`),
    ])));
  } catch (e) {
    weeklyStatus.textContent = e.message;
  }
}

if (weeklyList) loadWeekly();

const params = new URLSearchParams(location.search);
if (params.get("artist")) {
  artistInput.value = params.get("artist");
  titleInput.value = params.get("title") || "";
  findSimilar();
}
