"""Audio file normalization using ffmpeg.

Uploaded audio (WAV/MP3/FLAC/OGG/M4A) is normalized to:

    WAV, 48 kHz, 16-bit PCM, stereo
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".opus"}

TARGET_SAMPLE_RATE = 48000
TARGET_BIT_DEPTH = 16
TARGET_CHANNELS = 2


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


async def normalize(input_path: Path, output_path: Path) -> dict:
    """Normalize an audio file to WAV 48kHz/16-bit/stereo via ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-ac",
        str(TARGET_CHANNELS),
        "-sample_fmt",
        "s16",
        str(output_path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='replace')}")

    return await probe(output_path)


async def probe(path: Path) -> dict:
    """Read metadata (duration, sample rate, channels) from an audio file."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        return {}

    try:
        data = json.loads(stdout.decode())
    except json.JSONDecodeError:
        return {}

    audio_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {}
    )
    fmt = data.get("format", {})
    return {
        "format": Path(path).suffix.lstrip("."),
        "sample_rate": int(audio_stream.get("sample_rate", 0)),
        "channels": int(audio_stream.get("channels", 0)),
        "bit_depth": int(audio_stream.get("bits_per_sample", 0) or 0),
        "duration_seconds": float(audio_stream.get("duration", fmt.get("duration", 0)) or 0),
        "size_bytes": int(fmt.get("size", path.stat().st_size if path.exists() else 0)),
    }
