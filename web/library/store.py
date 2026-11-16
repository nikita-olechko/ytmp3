import os
import re
import shutil
from pathlib import Path

LIBRARY_DIR = os.environ.get("LIBRARY_DIR", "")


class LibraryError(Exception):
    pass


def enabled() -> bool:
    return bool(LIBRARY_DIR) and Path(LIBRARY_DIR).is_dir()


def _safe_name(title: str) -> str:
    name = re.sub(r'[\\/*?:"<>|\r\n]', " ", title)
    return re.sub(r"\s+", " ", name).strip()[:180] or "audio"


def _free_path(folder: Path, stem: str) -> Path:
    path = folder / f"{stem}.mp3"
    n = 2
    while path.exists():
        path = folder / f"{stem} ({n}).mp3"
        n += 1
    return path


def save(source: Path, title: str, folder: str = "") -> str:
    """Moves a converted MP3 into the music library (or another folder) and returns its file name."""
    folder = folder or LIBRARY_DIR
    if not folder or not Path(folder).is_dir():
        raise LibraryError("Saving to the library is not configured")
    dest = _free_path(Path(folder), _safe_name(title))
    partial = dest.with_name(f".{dest.name}.part")
    # Plain copy: the library may sit on another filesystem whose ACLs reject copying permissions.
    shutil.copyfile(source, partial)
    os.replace(partial, dest)
    source.unlink(missing_ok=True)
    return dest.name
