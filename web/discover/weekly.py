import os
from pathlib import Path

from web.discover.song import DISCOVER_DIR

EXPLO_DIR = os.environ.get("EXPLO_DIR", "")
AUDIO = {".flac", ".mp3", ".m4a", ".ogg", ".opus", ".wav", ".aac"}


class WeeklyError(Exception):
    pass


def enabled() -> bool:
    return bool(EXPLO_DIR and DISCOVER_DIR) and Path(EXPLO_DIR).is_dir()


def _root() -> Path:
    return Path(EXPLO_DIR).resolve()


def tracks() -> list[dict]:
    """Songs Explo downloaded for its current playlists, grouped by playlist folder."""
    found = []
    for path in sorted(_root().rglob("*")):
        if path.suffix.lower() in AUDIO and path.is_file() and not path.name.startswith("."):
            rel = path.relative_to(_root())
            found.append({"path": rel.as_posix(), "playlist": rel.parts[0] if len(rel.parts) > 1 else "",
                          "name": path.stem, "size": path.stat().st_size})
    return found


def keep(rel_path: str) -> str:
    """Moves one Explo download into DISCOVER_DIR so the next weekly clean-up leaves it alone."""
    source = (_root() / rel_path).resolve()
    if _root() not in source.parents or not source.is_file():
        raise WeeklyError("Not a weekly discovery file")
    dest = Path(DISCOVER_DIR) / source.name
    n = 2
    while dest.exists():
        dest = Path(DISCOVER_DIR) / f"{source.stem} ({n}){source.suffix}"
        n += 1
    os.replace(source, dest)
    return dest.name
