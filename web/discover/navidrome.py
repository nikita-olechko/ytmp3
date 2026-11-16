import hashlib
import os
import secrets

from web.discover.http import ServiceError, request_json
from web.discover.text import same_song

URL = os.environ.get("NAVIDROME_URL", "").rstrip("/")
USER = os.environ.get("NAVIDROME_USER", "")
PASSWORD = os.environ.get("NAVIDROME_PASSWORD", "")


def enabled() -> bool:
    return bool(URL and USER and PASSWORD)


def _call(method: str, **params) -> dict:
    salt = secrets.token_hex(8)
    auth = {"u": USER, "s": salt, "t": hashlib.md5((PASSWORD + salt).encode()).hexdigest(),
            "v": "1.16.1", "c": "ytmp3", "f": "json"}
    reply = request_json(f"{URL}/rest/{method}", {**auth, **params})["subsonic-response"]
    if reply.get("status") != "ok":
        raise ServiceError(f"Navidrome: {(reply.get('error') or {}).get('message', 'request failed')}")
    return reply


def now_playing() -> list[dict]:
    entries = _call("getNowPlaying").get("nowPlaying", {}).get("entry", [])
    return [{"artist": e.get("artist", ""), "title": e.get("title", ""), "album": e.get("album", ""),
             "user": e.get("username", ""), "minutes_ago": e.get("minutesAgo", 0)} for e in entries]


def has_song(artist: str, title: str) -> bool:
    songs = _call("search3", query=title, songCount=25, artistCount=0, albumCount=0).get("searchResult3", {}).get("song", [])
    return any(same_song(artist, title, s.get("artist", ""), s.get("title", "")) for s in songs)


def start_scan() -> None:
    _call("startScan")
