import os

from web.discover.http import ServiceError, request_json

API = "https://ws.audioscrobbler.com/2.0/"
API_KEY = os.environ.get("LASTFM_API_KEY", "")


def enabled() -> bool:
    return bool(API_KEY)


def _call(method: str, **params) -> dict:
    data = request_json(API, {"method": method, "api_key": API_KEY, "format": "json", "autocorrect": 1, **params})
    if "error" in data:
        raise ServiceError(f"Last.fm: {data.get('message', data['error'])}")
    return data


def _image(images: list) -> str:
    urls = [i.get("#text") for i in images or [] if i.get("#text")]
    return urls[-1] if urls else ""


def _track(t: dict, match: float) -> dict:
    return {
        "artist": t["artist"]["name"] if isinstance(t.get("artist"), dict) else t.get("artist", ""),
        "title": t["name"],
        "match": round(match, 3),
        "duration": int(t.get("duration") or 0) or None,
        "url": t.get("url", ""),
        "image": _image(t.get("image")),
    }


def similar_tracks(artist: str, title: str, limit: int = 40) -> list[dict]:
    tracks = _call("track.getSimilar", artist=artist, track=title, limit=limit).get("similartracks", {}).get("track", [])
    return [_track(t, float(t.get("match") or 0)) for t in tracks]


def similar_by_artist(artist: str, artists: int = 12, per_artist: int = 3) -> list[dict]:
    """Fallback for songs Last.fm has no track similarity for: top songs of similar artists."""
    similar = _call("artist.getSimilar", artist=artist, limit=artists).get("similarartists", {}).get("artist", [])
    found = []
    for a in similar:
        try:
            top = _call("artist.getTopTracks", artist=a["name"], limit=per_artist).get("toptracks", {}).get("track", [])
        except ServiceError:
            continue
        found += [_track(t, float(a.get("match") or 0)) for t in top]
    return found


def track_info(artist: str, title: str) -> dict:
    """Corrected artist/title and the album Last.fm associates with the song."""
    t = _call("track.getInfo", artist=artist, track=title).get("track", {})
    return {
        "artist": (t.get("artist") or {}).get("name", artist),
        "title": t.get("name", title),
        "album": (t.get("album") or {}).get("title", ""),
        "duration": int(t.get("duration") or 0) // 1000 or None,
    }
