#!/usr/bin/env python3
"""
Compress a video to under 50 MB using FFmpeg with H.265, CRF 28, slow preset.
Uses subprocess to call ffprobe and ffmpeg.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def require_ffmpeg() -> None:
    """Ensure ffmpeg and ffprobe are on PATH."""
    for name in ("ffprobe", "ffmpeg"):
        if shutil.which(name) is None:
            print(
                f"'{name}' not found. Install FFmpeg (e.g. brew install ffmpeg).",
                file=sys.stderr,
            )
            sys.exit(1)

# Paths
SRC = Path("/Users/myhomefolder/Downloads/Hardware_AWG/Meeting materials/2025-08-28/Hardware AWG meeting - 2025_08_28 07_50 PDT - Recording.mp4")
PROJECT_DIR = Path("/Users/myhomefolder/my-development/compression")
OUTPUT = PROJECT_DIR / "Hardware_AWG_2025_08_28_compressed.mp4"
TARGET_MB = 50
AUDIO_KBPS = 128  # reserve for audio in bitrate calculation


def get_duration_seconds(path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def main() -> None:
    require_ffmpeg()
    if not SRC.exists():
        print(f"Source file not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    print("Getting duration...")
    duration = get_duration_seconds(SRC)
    print(f"Duration: {duration:.1f} s")

    # Max total size 48 MB to stay under 50 MB
    target_bits = 48 * 8 * 1024 * 1024
    total_kbps = (target_bits / 1000) / duration
    video_max_kbps = int(total_kbps - AUDIO_KBPS)
    if video_max_kbps < 100:
        video_max_kbps = 100
    # buf size ~2× rate for VBV
    bufsize_kbps = video_max_kbps * 2

    print(f"Target: <{TARGET_MB} MB, video max ~{video_max_kbps} kbps")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(SRC),
        "-c:v", "libx265",
        "-preset", "slow",
        "-crf", "28",
        "-maxrate", f"{video_max_kbps}k",
        "-bufsize", f"{bufsize_kbps}k",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(OUTPUT),
    ]

    print("Running FFmpeg (H.265, CRF 28, slow preset)...")
    result = subprocess.run(ffmpeg_cmd)
    if result.returncode != 0:
        print("FFmpeg failed.", file=sys.stderr)
        sys.exit(result.returncode)

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Done. Output: {OUTPUT}")
    print(f"Size: {size_mb:.2f} MB")
    if size_mb > TARGET_MB:
        print(f"Warning: size exceeds {TARGET_MB} MB.", file=sys.stderr)


if __name__ == "__main__":
    main()
