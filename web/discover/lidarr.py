import os

from web.discover.http import ServiceError, request_json
from web.discover.text import normalize, same_artist

URL = os.environ.get("LIDARR_URL", "").rstrip("/")
API_KEY = os.environ.get("LIDARR_API_KEY", "")
ROOT_FOLDER = os.environ.get("LIDARR_ROOT_FOLDER", "/data/media/music/Library")
QUALITY_PROFILE = int(os.environ.get("LIDARR_QUALITY_PROFILE", "1"))
METADATA_PROFILE = int(os.environ.get("LIDARR_METADATA_PROFILE", "1"))


def enabled() -> bool:
    return bool(URL and API_KEY)


def _api(path: str, method: str = "GET", body=None, **params):
    return request_json(f"{URL}/api/v1/{path}", params or None, method, body, {"X-Api-Key": API_KEY})


def _find_album(artist: str, album: str) -> dict:
    for candidate in _api("album/lookup", term=f"{artist} {album}") or []:
        if normalize(candidate.get("title", "")) == normalize(album) and \
                same_artist(artist, candidate.get("artist", {}).get("artistName", "")):
            return candidate
    raise ServiceError(f"Lidarr doesn't know the album '{album}' by {artist}")


def _monitor_existing(album: dict) -> str:
    _api("album/monitor", "PUT", {"albumIds": [album["id"]], "monitored": True})
    artist = _api(f"artist/{album['artistId']}")
    if not artist.get("monitored"):
        artist["monitored"] = True
        _api(f"artist/{artist['id']}", "PUT", artist)
    return "requested (already in Lidarr, now wanted)"


def _add_new(album: dict) -> str:
    artist = album["artist"]
    if artist.get("id"):
        raise ServiceError("The artist is in Lidarr but this album isn't; open the artist in Lidarr and refresh it")
    artist.update({
        "qualityProfileId": QUALITY_PROFILE,
        "metadataProfileId": METADATA_PROFILE,
        "rootFolderPath": ROOT_FOLDER,
        "monitored": True,
        "monitorNewItems": "none",
        "addOptions": {"monitor": "none", "searchForMissingAlbums": False},
    })
    album.update({"monitored": True, "artist": artist, "addOptions": {"searchForNewAlbum": False}})
    _api("album", "POST", album)
    return "requested (added to Lidarr)"


def request_album(artist: str, album_title: str) -> dict:
    """Marks a studio album as wanted in Lidarr, adding the artist if needed; soularr then fetches it."""
    album = _find_album(artist, album_title)
    if album.get("albumType") != "Album":
        raise ServiceError(f"'{album['title']}' is a {album.get('albumType', 'release')}, not a studio album; get the song instead")
    status = _monitor_existing(album) if album.get("id") else _add_new(album)
    return {"album": album["title"], "artist": album["artist"]["artistName"], "status": status}
