"""
Audio separation using FFmpeg (extraction) and Demucs (vocal isolation).
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_path: str) -> str:
    """
    Extract the full audio track from *video_path* as a WAV file at 44100 Hz
    stereo and write it to *output_path*.

    Returns the output path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        output_path,
    ]
    logger.info("Extracting audio from %s -> %s", video_path, output_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr}")

    return output_path


def separate(audio_path: str, output_dir: str) -> dict[str, str]:
    """
    Run Demucs two-stem separation (vocals vs. background) on *audio_path*.

    Returns a dict with keys ``vocals_path`` and ``background_path``.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = [
        "python", "-m", "demucs",
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "-o", output_dir,
        audio_path,
    ]
    logger.info("Running Demucs separation on %s", audio_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Demucs separation failed: {result.stderr}")

    # Demucs outputs into <output_dir>/htdemucs/<stem_name>/vocals.wav etc.
    stem_name = Path(audio_path).stem
    demucs_out = os.path.join(output_dir, "htdemucs", stem_name)

    vocals_path = os.path.join(demucs_out, "vocals.wav")
    background_path = os.path.join(demucs_out, "no_vocals.wav")

    if not os.path.isfile(vocals_path):
        raise FileNotFoundError(f"Demucs did not produce vocals file at {vocals_path}")
    if not os.path.isfile(background_path):
        raise FileNotFoundError(
            f"Demucs did not produce background file at {background_path}"
        )

    logger.info("Separation complete: vocals=%s, background=%s", vocals_path, background_path)
    return {
        "vocals_path": vocals_path,
        "background_path": background_path,
    }


def separate_from_video(video_path: str, work_dir: str) -> dict[str, str]:
    """
    End-to-end helper: extract audio from video, then separate vocals.

    Returns a dict with ``vocals_path``, ``background_path``, and
    ``original_audio_path``.
    """
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    original_audio_path = os.path.join(work_dir, "original_audio.wav")
    extract_audio(video_path, original_audio_path)

    separation_dir = os.path.join(work_dir, "separated")
    parts = separate(original_audio_path, separation_dir)

    return {
        "vocals_path": parts["vocals_path"],
        "background_path": parts["background_path"],
        "original_audio_path": original_audio_path,
    }
