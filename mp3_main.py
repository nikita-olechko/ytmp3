#!/usr/bin/env python3
"""
YouTube to MP3/MP4 Converter - Main Script

This script provides a programmatic interface to convert YouTube videos to MP3 or MP4 format.
It extracts the core functionality from the ytconverter package for easy integration.
"""

import re

from utils.utils import download_single_mp3

# Constants
URLS = [
    "https://www.youtube.com/watch?v=AARDtj6wL3U&t=2670s", # karaoke
]

QUALITY = 256  # Bitrate for MP3 (e.g., 320, 256, 192, 128, 96). Can also use 'best' for best available quality.


URL_RE = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$")


def main():
    """Run the converter functions."""

    print("YouTube to MP3 Converter")
    print("=" * 40)

    # Convert to MP3
    print("\nConverting to MP3...")
    for url in URLS:
        success, message = download_single_mp3(url, str(QUALITY),
                                               download_path="./audio",
                                               verbose=True)
        status = "✓" if success else "✗"
        print(f"{status} {message}")

    print("\nEnd.")


if __name__ == "__main__":
    main()
