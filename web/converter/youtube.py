import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

URL_RE = re.compile(r"^(https?://)?([\w-]+\.)?(youtube\.com|youtu\.be)/.+$")
QUALITIES = ("320", "256", "192", "128")
COOKIES_PATH = os.environ.get("YTDLP_COOKIES", "/secrets/cookies.txt")


@dataclass
class ConvertedFile:
    path: Path
    title: str
    workdir: Path

    def cleanup(self) -> None:
        shutil.rmtree(self.workdir, ignore_errors=True)


class ConversionError(Exception):
    pass


def to_mp3(url: str, quality: str = "192") -> ConvertedFile:
    """Downloads a single YouTube video's audio into a temp dir and converts it to MP3."""
    if not URL_RE.match(url):
        raise ConversionError("Not a YouTube URL")
    if quality not in QUALITIES:
        quality = "192"

    workdir = Path(tempfile.mkdtemp(prefix="ytmp3-"))
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality},
        ],
    }
    if os.path.exists(COOKIES_PATH):
        # yt-dlp rewrites its cookie file, and the mounted secret is read-only
        cookie_copy = workdir / "cookies.txt"
        shutil.copyfile(COOKIES_PATH, cookie_copy)
        opts["cookiefile"] = str(cookie_copy)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        shutil.rmtree(workdir, ignore_errors=True)
        raise ConversionError(str(e)) from e

    mp3s = list(workdir.glob("*.mp3"))
    if not mp3s:
        shutil.rmtree(workdir, ignore_errors=True)
        raise ConversionError("Conversion produced no file")
    return ConvertedFile(path=mp3s[0], title=info.get("title") or "audio", workdir=workdir)
