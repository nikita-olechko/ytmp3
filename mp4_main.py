#!/usr/bin/env python3
"""
YouTube to MP4 Converter - Main Script

This script provides a programmatic interface to download YouTube videos
as MP4 format using the shared utility functions.
"""

from utils.utils import download_single_mp4

# Constants
URLS = [
    "https://www.youtube.com/watch?v=AARDtj6wL3U&t=2670s
]

QUALITY = "1080"  # Examples: "best", "1080", "720", "480", "360"


def main() -> None:
    """Run MP4 downloads for all URLs."""
    print("YouTube to MP4 Converter")
    print("=" * 40)

    print("\nDownloading MP4 files...")
    for url in URLS:
        success, message = download_single_mp4(
            url,
            quality=QUALITY,
            # No custom path: defaults to repository `video/` folder in utils.
            download_path=None,
        )
        status = "[OK]" if success else "[X]"
        print(f"{status} {message}")

    print("\nEnd.")


if __name__ == "__main__":
    main()

