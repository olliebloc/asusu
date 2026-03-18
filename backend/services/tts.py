"""
Text-to-speech generation via the ElevenLabs API.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

import requests

from config.settings import settings

logger = logging.getLogger(__name__)

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"


def _get_audio_duration(file_path: str) -> float:
    """Return the duration (seconds) of an audio file via ffprobe."""
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


def generate_segment(
    text: str,
    voice_id: str,
    output_path: str,
    target_duration: Optional[float] = None,
) -> dict[str, Any]:
    """
    Synthesise *text* with the given ElevenLabs *voice_id* and write the
    resulting MP3 to *output_path*.

    Returns a dict with ``output_path`` and ``duration``.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    url = f"{ELEVENLABS_TTS_URL}/{voice_id}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    body: dict[str, Any] = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    response = requests.post(url, json=body, headers=headers, timeout=60)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    duration = _get_audio_duration(output_path)

    logger.debug(
        "TTS segment written: %s (%.2fs, target=%.2fs)",
        output_path,
        duration,
        target_duration or 0,
    )

    return {
        "output_path": output_path,
        "duration": duration,
    }


def generate_all_segments(
    translated_segments: list[dict[str, Any]],
    target_lang: str,
    output_dir: str,
    voice_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Generate TTS audio for every segment in *translated_segments*.

    Uses the language-default voice from settings when *voice_id* is ``None``.

    Returns a list of dicts, each containing the original segment timing plus
    ``tts_path`` and ``tts_duration``.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if voice_id is None:
        lang_info = settings.SUPPORTED_LANGUAGES.get(target_lang, {})
        voice_id = lang_info.get("voice_id", "pNInz6obpgDQGcFmaJgB")

    results: list[dict[str, Any]] = []
    total = len(translated_segments)

    for idx, seg in enumerate(translated_segments):
        text = seg.get("translated_text", "")
        if not text.strip():
            logger.warning("Segment %d/%d has empty text, skipping TTS", idx + 1, total)
            continue

        seg_path = os.path.join(output_dir, f"segment_{idx:04d}.mp3")
        target_duration = seg.get("end", 0) - seg.get("start", 0)

        try:
            tts_result = generate_segment(
                text=text,
                voice_id=voice_id,
                output_path=seg_path,
                target_duration=target_duration if target_duration > 0 else None,
            )
            results.append(
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "original_text": seg.get("original_text", ""),
                    "translated_text": text,
                    "tts_path": tts_result["output_path"],
                    "tts_duration": tts_result["duration"],
                }
            )
            logger.info(
                "TTS segment %d/%d complete (%.2fs)",
                idx + 1,
                total,
                tts_result["duration"],
            )
        except Exception:
            logger.exception(
                "TTS failed for segment %d/%d, skipping", idx + 1, total
            )
            continue

    logger.info(
        "TTS generation complete: %d/%d segments produced",
        len(results),
        total,
    )
    return results
