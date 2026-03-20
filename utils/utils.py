import os
import platform
import re
import subprocess as sp
import time
from pathlib import Path
from typing import Optional, Tuple
import yt_dlp

URL_RE = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$")


def is_android() -> bool:
    """Check if running on Android (Termux)."""
    env = os.environ
    return any(
        k in env for k in ("ANDROID_ROOT", "TERMUX_VERSION")
    ) or "com.termux" in env.get("HOME", "")


def get_download_path(format_str: str, custom_path: Optional[str] = None) -> str:
    """
    Get the download path for the specified format.

    Args:
        format_str: The format type ('mp3' or 'mp4')
        custom_path: Optional custom download path

    Returns:
        The download path as a string
    """
    if custom_path:
        final_path = Path(custom_path)
        final_path.mkdir(parents=True, exist_ok=True)
        return str(final_path)

    system = platform.system()
    home = Path.home()

    if system == "Windows":
        base = home / "Downloads"
    elif system == "Darwin":
        base = home / "Downloads"
    elif is_android():
        base = Path("/storage/emulated/0/Download")
    else:
        base = home / "Downloads"

    if format_str.lower() == "mp3":
        default = base / "audio"
    elif format_str.lower() == "mp4":
        default = base / "videos"
    else:
        default = base

    final_path = default
    final_path.mkdir(parents=True, exist_ok=True)
    return str(final_path)


def sanitize_filename(name: str) -> str:
    """Sanitize filename by removing invalid characters."""
    bad_chars = re.compile(r'[\\/*?:"<>|]')
    return bad_chars.sub("", name)


def get_video_info(url: str) -> dict:
    """
    Get video information using yt-dlp.

    Args:
        url: YouTube URL

    Returns:
        Video information dictionary

    Raises:
        Exception: If video info cannot be retrieved
    """
    try:
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        raise Exception(f"Failed to get video info: {e}")


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        sp.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (sp.CalledProcessError, FileNotFoundError):
        return False


def download_single_mp3(
        url: str,
        quality: str = "best",
        download_path: Optional[str] = None,
        verbose: bool = True
) -> Tuple[bool, str]:
    """
    Download a single video as MP3.

    Args:
        url: YouTube URL
        quality: Audio quality ('best', '320', '256', '192', '128', '96')
        download_path: Custom download path
        verbose: Whether to print progress messages

    Returns:
        Tuple of (success, message)
    """
    if not URL_RE.match(url):
        return False, "Invalid URL"

    # Check for FFmpeg
    if not check_ffmpeg():
        return False, "FFmpeg not found. Please install FFmpeg to convert audio files."

    try:
        if verbose:
            print(f"Fetching audio information for: {url}")

        info = get_video_info(url)
        title = sanitize_filename(info.get("title", "Unknown"))

        if verbose:
            print(f"Title: {title}")

        # Get download path
        dest = Path(get_download_path("mp3", download_path))

        # Set up yt-dlp options
        if quality == "best":
            dl_format = "bestaudio/best"
        else:
            dl_format = f"bestaudio[abr<={quality}]/best"

        ydl_opts = {
            "format": dl_format,
            "outtmpl": str(dest / f"{title}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality if quality != "best" else "192",
                }
            ],
            "quiet": not verbose,
        }

        if verbose:
            print("Starting download...")

        start_time = time.time()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        elapsed_time = int(time.time() - start_time)

        if verbose:
            print(f"MP3 downloaded successfully in {elapsed_time} seconds")

        return True, f"Downloaded: {title}"

    except Exception as e:
        error_msg = str(e)
        if "ffprobe and ffmpeg not found" in error_msg:
            return False, "FFmpeg not found. Please install FFmpeg to convert audio files."
        return False, f"Download failed: {error_msg}"


def download_single_mp4(
        url: str,
        quality: str = "best",
        download_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Download a single video as MP4.

    Args:
        url: YouTube URL
        quality: Video quality ('best', '1080', '720', '480', '360')
        download_path: Optional custom output path

    Returns:
        Tuple of (success, message)
    """
    if not URL_RE.match(url):
        return False, "Invalid URL"

    if not check_ffmpeg():
        return False, "FFmpeg not found. Please install FFmpeg to process video files."

    try:
        info = get_video_info(url)
        title = sanitize_filename(info.get("title", "Unknown"))

        if download_path:
            dest = Path(get_download_path("mp4", download_path))
        else:
            # Default MP4 output to the repo's video folder.
            dest = Path(__file__).resolve().parent.parent / "video"
            dest.mkdir(parents=True, exist_ok=True)

        if quality == "best":
            dl_format = "bestvideo+bestaudio/best"
        else:
            dl_format = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

        ydl_opts = {
            "format": dl_format,
            "outtmpl": str(dest / f"{title}.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return True, f"Downloaded: {title}"

    except Exception as e:
        error_msg = str(e)
        if "ffprobe and ffmpeg not found" in error_msg:
            return False, "FFmpeg not found. Please install FFmpeg to process video files."
        return False, f"Download failed: {error_msg}"
