"""
Segment-level translation via the Anthropic Claude API, optimised for dubbing.
"""

import logging
import re
from typing import Any, Optional

import anthropic

from config.settings import settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
BATCH_SIZE = 50

SYSTEM_PROMPT = """\
You are a professional dubbing translator. Your task is to translate speech \
segments for video dubbing.

Rules:
- Produce natural, conversational translations suitable for spoken audio.
- Preserve the original tone, emotion, and register.
- Keep translated segments at roughly the same length as the originals so the \
  dubbed audio fits the original timing.
- Do NOT translate proper nouns (names of people, brands, places) — keep them \
  as-is.
- Maintain any technical terms where a direct equivalent does not exist in the \
  target language.
- Return ONLY the translated lines in the exact same numbered format provided. \
  Do not add commentary or explanations.\
"""


def _build_user_prompt(
    segments: list[dict[str, Any]],
    source_lang: str,
    target_lang: str,
    context: str,
    offset: int,
) -> str:
    """Format a batch of segments for the Claude prompt."""
    lines: list[str] = []
    lines.append(
        f"Translate the following segments from {source_lang} to {target_lang}."
    )
    if context:
        lines.append(f"Context about this video: {context}")
    lines.append("")
    lines.append(
        "Each line is formatted as: [index] (start_seconds-end_seconds): text"
    )
    lines.append("Return ONLY the translated lines in the same format.")
    lines.append("")

    for idx, seg in enumerate(segments):
        global_idx = offset + idx
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        lines.append(f"[{global_idx}] ({start:.2f}-{end:.2f}): {text}")

    return "\n".join(lines)


_LINE_RE = re.compile(
    r"\[(\d+)\]\s*\((\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\):\s*(.+)"
)


def _parse_response(
    response_text: str,
    original_segments: list[dict[str, Any]],
    offset: int,
) -> list[dict[str, Any]]:
    """Parse Claude's response back into structured translated segments."""
    translated: list[dict[str, Any]] = []
    lookup: dict[int, dict[str, Any]] = {
        offset + i: seg for i, seg in enumerate(original_segments)
    }

    for line in response_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        match = _LINE_RE.match(line)
        if not match:
            continue

        idx = int(match.group(1))
        start = float(match.group(2))
        end = float(match.group(3))
        translated_text = match.group(4).strip()

        orig = lookup.get(idx)
        original_text = orig["text"] if orig else ""

        translated.append(
            {
                "start": start,
                "end": end,
                "original_text": original_text,
                "translated_text": translated_text,
            }
        )

    return translated


def translate_segments(
    segments: list[dict[str, Any]],
    source_lang: str,
    target_lang: str,
    context: str = "",
) -> list[dict[str, Any]]:
    """
    Translate a list of transcription segments from *source_lang* to
    *target_lang* using Claude.

    Segments are sent in batches of ``BATCH_SIZE`` to stay within reasonable
    prompt sizes.

    Returns a list of dicts, each with ``start``, ``end``, ``original_text``
    and ``translated_text``.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    all_translated: list[dict[str, Any]] = []

    total_batches = (len(segments) + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(
        "Translating %d segments (%s -> %s) in %d batch(es)",
        len(segments),
        source_lang,
        target_lang,
        total_batches,
    )

    for batch_num in range(total_batches):
        offset = batch_num * BATCH_SIZE
        batch = segments[offset : offset + BATCH_SIZE]

        user_prompt = _build_user_prompt(
            batch, source_lang, target_lang, context, offset
        )

        logger.info(
            "Sending batch %d/%d (%d segments) to Claude",
            batch_num + 1,
            total_batches,
            len(batch),
        )

        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = message.content[0].text  # type: ignore[union-attr]
        parsed = _parse_response(response_text, batch, offset)
        all_translated.extend(parsed)

        logger.info(
            "Batch %d/%d: parsed %d translated segments",
            batch_num + 1,
            total_batches,
            len(parsed),
        )

    logger.info("Translation complete: %d segments", len(all_translated))
    return all_translated
