from dataclasses import asdict, dataclass

import yt_dlp

MAX_RESULTS = 25


@dataclass
class SearchResult:
    id: str
    title: str
    channel: str
    duration: int | None
    url: str
    thumbnail: str


class SearchError(Exception):
    pass


def search(query: str, limit: int = 10) -> list[dict]:
    """Searches YouTube for videos matching the query, without downloading anything."""
    query = query.strip()
    if not query:
        raise SearchError("Empty search")
    limit = max(1, min(limit, MAX_RESULTS))

    opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist"}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    except Exception as e:
        raise SearchError(str(e)) from e

    results = []
    for entry in info.get("entries") or []:
        video_id = entry.get("id")
        if not video_id:
            continue
        results.append(asdict(SearchResult(
            id=video_id,
            title=entry.get("title") or video_id,
            channel=entry.get("channel") or entry.get("uploader") or "",
            duration=int(entry["duration"]) if entry.get("duration") else None,
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail=f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
        )))
    return results
