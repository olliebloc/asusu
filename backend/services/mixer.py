"""
Audio mixing and video muxing using FFmpeg.

Assembles individually generated TTS segments on top of the separated
background audio track, then replaces the original video's audio with the
dubbed mix.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_audio_duration(file_path: str) -> float:
    """Return the duration (seconds) of a media file via ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def assemble_dubbed_audio(
    tts_segments: list[dict[str, Any]],
    background_audio_path: str,
    total_duration: float,
    output_path: str,
) -> str:
    """
    Mix all TTS segment files on top of the background audio track, placing
    each segment at its designated start time.

    Each entry in *tts_segments* must contain at least ``start`` (float,
    seconds) and ``tts_path`` (str, path to the MP3/WAV file).

    The resulting AAC file is written to *output_path*.

    Returns the output path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if not tts_segments:
        raise ValueError("No TTS segments provided for mixing")

    # ---- Build the FFmpeg command with a complex filter graph ---------------
    input_args: list[str] = []
    filter_parts: list[str] = []

    # Input 0: background audio
    input_args.extend(["-i", background_audio_path])

    # Inputs 1..N: each TTS segment
    for idx, seg in enumerate(tts_segments):
        input_args.extend(["-i", seg["tts_path"]])

    # Background: pad to total_duration so it never ends early
    filter_parts.append(
        f"[0:a]apad=whole_dur={total_duration}[bg]"
    )

    # Each TTS segment: delay to its start time, then pad to total_duration
    mix_inputs: list[str] = ["[bg]"]
    weights: list[str] = ["1"]

    for idx, seg in enumerate(tts_segments):
        input_idx = idx + 1  # 0 is background
        delay_ms = int(seg["start"] * 1000)
        label = f"tts{idx}"
        filter_parts.append(
            f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={total_duration}[{label}]"
        )
        mix_inputs.append(f"[{label}]")
        weights.append("2")

    # Combine everything with amix
    n_inputs = len(mix_inputs)
    weight_str = " ".join(weights)
    mix_input_str = "".join(mix_inputs)
    filter_parts.append(
        f"{mix_input_str}amix=inputs={n_inputs}:duration=first:weights={weight_str}[out]"
    )

    filter_graph = ";\n".join(filter_parts)

    cmd = [
        "ffmpeg",
        "-y",
        *input_args,
        "-filter_complex", filter_graph,
        "-map", "[out]",
        "-acodec", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-t", str(total_duration),
        output_path,
    ]

    logger.info(
        "Assembling dubbed audio: %d TTS segments + background -> %s",
        len(tts_segments),
        output_path,
    )
    logger.debug("FFmpeg filter graph:\n%s", filter_graph)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg stderr:\n%s", result.stderr)
        raise RuntimeError(f"FFmpeg audio assembly failed: {result.stderr}")

    duration = _get_audio_duration(output_path)
    logger.info("Dubbed audio assembled: %s (%.1fs)", output_path, duration)

    return output_path


def mux_video(
    original_video_path: str,
    dubbed_audio_path: str,
    output_path: str,
) -> str:
    """
    Replace the audio track of *original_video_path* with *dubbed_audio_path*,
    copying the video stream as-is.

    Returns the output path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", original_video_path,
        "-i", dubbed_audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]

    logger.info(
        "Muxing video %s + audio %s -> %s",
        original_video_path,
        dubbed_audio_path,
        output_path,
    )

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg stderr:\n%s", result.stderr)
        raise RuntimeError(f"FFmpeg muxing failed: {result.stderr}")

    logger.info("Muxed video written: %s", output_path)
    return output_path
