import os
import subprocess

from web.converter.youtube import ConversionError, to_mp3
from web.discover.text import words
from web.library.store import save
from web.search.youtube import search

DISCOVER_DIR = os.environ.get("DISCOVER_DIR", "")
QUALITY = "320"
AVOID = ("live", "cover", "karaoke", "instrumental", "remix", "reaction", "8d", "slowed", "sped up", "nightcore",
         "acoustic", "version", "session", "concert", "tour", "extended", "pmv", "amv")


def enabled() -> bool:
    return bool(DISCOVER_DIR) and os.path.isdir(DISCOVER_DIR)


def _score(result: dict, artist: str, title: str, duration: int | None) -> float:
    name, channel = f" {words(result['title'])} ", words(result["channel"])
    wanted, by = f" {words(title)} ", words(artist)
    score = 3.0 if wanted in name else 0.0
    if f" {by} " in name or by in channel:
        score += 2
    if channel == by or result["channel"].endswith(" - Topic"):
        score += 1.5
    if duration and result["duration"]:
        score += 2 if abs(result["duration"] - duration) <= 10 else -2
    if " official audio " in name or " audio " in name:
        score += 1
    if " lyrics " in name or " lyric " in name:
        score -= 0.5
    score -= sum(3 for word in AVOID if f" {word} " in name and f" {word} " not in wanted)
    return score


def best_video(artist: str, title: str, duration: int | None) -> dict:
    results = search(f"{artist} - {title}", 8)
    if not results:
        raise ConversionError("No YouTube results")
    best = max(results, key=lambda r: _score(r, artist, title, duration))
    if _score(best, artist, title, duration) < 3:
        raise ConversionError(f"No convincing YouTube match (best: {best['title']})")
    return best


def _retag(path, artist: str, title: str, album: str) -> None:
    tagged = path.with_name("tagged.mp3")
    tags = ["-metadata", f"artist={artist}", "-metadata", f"title={title}", "-metadata", f"album_artist={artist}"]
    if album:
        tags += ["-metadata", f"album={album}"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-map", "0", "-c", "copy", "-id3v2_version", "3",
                    *tags, str(tagged)], check=True, capture_output=True)
    os.replace(tagged, path)


def fetch(artist: str, title: str, album: str = "", duration: int | None = None) -> dict:
    """Downloads the best YouTube match for a song, tags it with the given names and saves it to DISCOVER_DIR."""
    video = best_video(artist, title, duration)
    result = to_mp3(video["url"], QUALITY, embed_metadata=True)
    try:
        _retag(result.path, artist, title, album)
        name = save(result.path, f"{artist} - {title}", DISCOVER_DIR)
    finally:
        result.cleanup()
    return {"saved": name, "video": video["title"]}
