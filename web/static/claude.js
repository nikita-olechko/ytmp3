const claudeButton = document.getElementById("claude-copy");
const claudeTtl = document.getElementById("claude-ttl");
const claudeStatus = document.getElementById("claude-status");

function claudeInstructions(base, token, expiresAt) {
  const expiry = new Date(expiresAt * 1000).toLocaleString();
  return `You can use my ytmp3 API to search YouTube and download songs as MP3s.
Base URL: ${base}
Token (expires ${expiry}): ${token}
Send it on every request as: Authorization: Bearer <token>

Search (returns JSON {results: [{title, channel, duration, url, ...}]}, limit 1-25):
  curl -s -G -H "Authorization: Bearer ${token}" --data-urlencode "q=SONG NAME" -d limit=5 ${base}/api/search

Download one video as MP3 (quality: 320, 256, 192 or 128; saves with the video title as the filename):
  curl -s -f -OJ -H "Authorization: Bearer ${token}" -H "Content-Type: application/json" -d '{"url":"https://www.youtube.com/watch?v=ID","quality":"192"}' ${base}/api/convert

Notes: convert one URL per request, sequentially (each can take up to a few minutes). Errors return JSON {error}. 401 means the token expired; ask me for a new one. Save files to the folder I ask for (use curl --output-dir), otherwise the current directory. Pick the official or best-matching upload when searching for a song.`;
}

claudeButton.addEventListener("click", async () => {
  claudeStatus.textContent = "Creating token…";
  try {
    const res = await fetch("/api/tokens", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hours: Number(claudeTtl.value) }),
    });
    if (res.status === 401) {
      location.href = "/login";
      return;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    await navigator.clipboard.writeText(claudeInstructions(location.origin, data.token, data.expires_at));
    claudeStatus.textContent = `Copied. Token expires ${new Date(data.expires_at * 1000).toLocaleString()}.`;
  } catch (err) {
    claudeStatus.textContent = err.message;
  }
});
