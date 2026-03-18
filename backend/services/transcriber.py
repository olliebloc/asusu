"""
Speech-to-text transcription using OpenAI Whisper (local model).
"""

import logging
from typing import Any, Optional

import whisper  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model: Optional[whisper.Whisper] = None


def _get_model() -> whisper.Whisper:
    """Load the Whisper ``base`` model on first call, then cache it."""
    global _model
    if _model is None:
        logger.info("Loading Whisper 'base' model (first call)...")
        _model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    return _model


def transcribe(
    audio_path: str,
    language: Optional[str] = None,
) -> dict[str, Any]:
    """
    Transcribe *audio_path* and return segments without word-level timestamps.

    Returns::

        {
            "text": "full transcript ...",
            "segments": [{"start": 0.0, "end": 2.5, "text": "..."}],
            "language": "en",
        }
    """
    model = _get_model()

    kwargs: dict[str, Any] = {}
    if language:
        kwargs["language"] = language

    logger.info("Transcribing %s (language=%s)", audio_path, language or "auto")
    result = model.transcribe(audio_path, **kwargs)

    segments = [
        {
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "text": seg["text"].strip(),
        }
        for seg in result["segments"]
    ]

    detected_lang: str = result.get("language", language or "unknown")
    logger.info(
        "Transcription complete: %d segments, language=%s",
        len(segments),
        detected_lang,
    )

    return {
        "text": result["text"].strip(),
        "segments": segments,
        "language": detected_lang,
    }


def transcribe_with_words(
    audio_path: str,
    language: Optional[str] = None,
) -> dict[str, Any]:
    """
    Like :func:`transcribe` but with ``word_timestamps=True``.

    Each segment includes a ``words`` list with per-word timing.
    """
    model = _get_model()

    kwargs: dict[str, Any] = {"word_timestamps": True}
    if language:
        kwargs["language"] = language

    logger.info(
        "Transcribing with word timestamps %s (language=%s)",
        audio_path,
        language or "auto",
    )
    result = model.transcribe(audio_path, **kwargs)

    segments = []
    for seg in result["segments"]:
        words = [
            {
                "start": float(w["start"]),
                "end": float(w["end"]),
                "text": w["word"].strip(),
            }
            for w in seg.get("words", [])
        ]
        segments.append(
            {
                "start": float(seg["start"]),
                "end": float(seg["end"]),
                "text": seg["text"].strip(),
                "words": words,
            }
        )

    detected_lang: str = result.get("language", language or "unknown")
    logger.info(
        "Transcription (words) complete: %d segments, language=%s",
        len(segments),
        detected_lang,
    )

    return {
        "text": result["text"].strip(),
        "segments": segments,
        "language": detected_lang,
    }
