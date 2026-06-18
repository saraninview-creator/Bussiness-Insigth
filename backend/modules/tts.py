"""
TTS Module — converts script segments to audio using edge-tts,
then concatenates them into a single combined.mp3 using ffmpeg.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import edge_tts

VOICE = "en-US-AriaNeural"


async def _synthesize_one(text: str, output_path: str) -> None:
    """Synthesize a single text segment to an mp3 file."""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)


def synthesize_segments(
    segments: list[dict[str, Any]], audio_dir: str
) -> list[dict[str, Any]]:
    """
    Synthesize each segment to an mp3 in audio_dir.
    Returns segments enriched with audio_file, start_ms, end_ms.
    """
    audio_dir_path = Path(audio_dir)
    audio_dir_path.mkdir(parents=True, exist_ok=True)

    enriched = []
    current_ms = 0

    for i, seg in enumerate(segments):
        text = seg["text"]
        out_file = str(audio_dir_path / f"seg_{i:02d}.mp3")

        # Run async synthesis in a clean event loop
        asyncio.run(_synthesize_one(text, out_file))

        # Measure actual duration via ffprobe
        duration_ms = _probe_duration_ms(out_file)
        if duration_ms is None:
            # fallback: estimated
            duration_ms = int(seg.get("estimated_duration_seconds", 5) * 1000)

        enriched.append(
            {
                **seg,
                "audio_file": out_file,
                "start_ms": current_ms,
                "end_ms": current_ms + duration_ms,
                "duration_ms": duration_ms,
            }
        )
        current_ms += duration_ms

    return enriched


def _probe_duration_ms(filepath: str) -> int | None:
    """Use mutagen to get audio duration in milliseconds."""
    try:
        from mutagen.mp3 import MP3
        audio = MP3(filepath)
        if audio.info.length:
            return int(audio.info.length * 1000)
    except Exception:
        pass
    return None


def concatenate_audio(segments: list[dict[str, Any]], output_path: str) -> None:
    """Concatenate per-segment mp3 files into a single combined.mp3 using ffmpeg."""
    audio_files = [s["audio_file"] for s in segments if os.path.exists(s.get("audio_file", ""))]
    if not audio_files:
        raise RuntimeError("No audio segments to concatenate.")

    # Write ffmpeg concat list
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        concat_file = f.name
        for af in audio_files:
            f.write(f"file '{af}'\n")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                output_path,
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    finally:
        os.unlink(concat_file)
