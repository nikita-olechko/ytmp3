import subprocess
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, render_template, request

from web.auth.guard import login_required
from web.converter.youtube import ConversionError
from web.discover import lastfm, lidarr, navidrome, song, weekly
from web.discover.http import ServiceError
from web.discover.text import normalize
from web.library.store import LibraryError

discover_bp = Blueprint("discover", __name__)

LOOKUP_THREADS = 8


def _body() -> dict:
    return request.get_json(silent=True) or {}


def _fields(source: dict, *names) -> list[str]:
    return [(source.get(n) or "").strip() for n in names]


def _unavailable(name: str):
    return jsonify(error=f"{name} is not configured"), 404


def _mark_owned(tracks: list[dict]) -> list[dict]:
    def owned(t):
        try:
            return navidrome.has_song(t["artist"], t["title"])
        except ServiceError:
            return None
    with ThreadPoolExecutor(LOOKUP_THREADS) as pool:
        for t, has in zip(tracks, pool.map(owned, tracks)):
            t["in_library"] = has
    return tracks


def _dedupe(tracks: list[dict], seed_artist: str, seed_title: str) -> list[dict]:
    seen, unique = {(normalize(seed_artist), normalize(seed_title))}, []
    for t in tracks:
        key = (normalize(t["artist"]), normalize(t["title"]))
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


@discover_bp.get("/discover")
@login_required
def page():
    return render_template("discover.html", weekly=weekly.enabled(), lidarr=lidarr.enabled(),
                           now_playing=navidrome.enabled(), songs=song.enabled())


@discover_bp.get("/api/discover/now-playing")
@login_required
def now_playing():
    if not navidrome.enabled():
        return _unavailable("Navidrome")
    try:
        return jsonify(playing=navidrome.now_playing())
    except ServiceError as e:
        return jsonify(error=str(e)), 502


@discover_bp.get("/api/discover/similar")
@login_required
def similar():
    if not lastfm.enabled():
        return _unavailable("Last.fm")
    artist, title = _fields(request.args, "artist", "title")
    if not artist:
        return jsonify(error="Enter an artist"), 400
    limit = max(5, min(request.args.get("limit", 40, type=int), 100))
    try:
        tracks = lastfm.similar_tracks(artist, title, limit) if title else []
        source = "similar songs"
        if not tracks:
            tracks, source = lastfm.similar_by_artist(artist), "top songs of similar artists"
    except ServiceError as e:
        return jsonify(error=str(e)), 502
    tracks = _dedupe(tracks, artist, title)[:limit]
    if navidrome.enabled():
        _mark_owned(tracks)
    return jsonify(source=source, tracks=tracks)


@discover_bp.post("/api/discover/song")
@login_required
def get_song():
    if not song.enabled():
        return _unavailable("Saving discovered songs")
    artist, title, album = _fields(_body(), "artist", "title", "album")
    if not (artist and title):
        return jsonify(error="Artist and title are required"), 400
    try:
        if not album and lastfm.enabled():
            album = lastfm.track_info(artist, title)["album"]
        result = song.fetch(artist, title, album, _body().get("duration"))
    except (ConversionError, LibraryError, ServiceError, subprocess.CalledProcessError) as e:
        return jsonify(error=str(e)), 400
    if navidrome.enabled():
        try:
            navidrome.start_scan()
        except ServiceError:
            pass
    return jsonify(result)


@discover_bp.post("/api/discover/album")
@login_required
def get_album():
    if not (lidarr.enabled() and lastfm.enabled()):
        return _unavailable("Lidarr")
    artist, title, album = _fields(_body(), "artist", "title", "album")
    try:
        if not album:
            album = lastfm.track_info(artist, title)["album"]
        if not album:
            return jsonify(error="Last.fm doesn't know which album this song is on"), 404
        return jsonify(lidarr.request_album(artist, album))
    except ServiceError as e:
        return jsonify(error=str(e)), 400


@discover_bp.get("/api/discover/weekly")
@login_required
def weekly_tracks():
    if not weekly.enabled():
        return _unavailable("Weekly discovery")
    return jsonify(tracks=weekly.tracks())


@discover_bp.post("/api/discover/weekly/keep")
@login_required
def keep_weekly():
    if not weekly.enabled():
        return _unavailable("Weekly discovery")
    try:
        return jsonify(kept=weekly.keep(_body().get("path") or ""))
    except (weekly.WeeklyError, OSError) as e:
        return jsonify(error=str(e)), 400
