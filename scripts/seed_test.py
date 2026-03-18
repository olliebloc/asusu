#!/usr/bin/env python3
"""
Seed test script for the Asusu dubbing pipeline.

Runs the full pipeline end-to-end using stubs for external services:
  - Translator: returns original text with a "[LANG]" prefix
  - TTS: generates silence via ffmpeg
  - Storage: saves to local filesystem and returns file:// URLs

Usage:
    python scripts/seed_test.py --video_url https://example.com/sample.mp4 --target_lang es
    python scripts/seed_test.py --video_url /path/to/local/video.mp4 --target_lang fr
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path


# ---------------------------------------------------------------------------
# Stub implementations
# ---------------------------------------------------------------------------

class StubTranslator:
    """Stub translator that prefixes each text segment with [LANG]."""

    def __init__(self, target_lang: str) -> None:
        self.target_lang = target_lang

    def translate(self, segments: list[dict]) -> list[dict]:
        translated = []
        for seg in segments:
            translated.append({
                **seg,
                "translated_text": f"[{self.target_lang.upper()}] {seg['text']}",
            })
        return translated


class StubTTS:
    """Stub TTS that generates silent audio clips via ffmpeg."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def synthesize(self, segments: list[dict]) -> list[dict]:
        results = []
        for i, seg in enumerate(segments):
            duration = seg.get("end", 1.0) - seg.get("start", 0.0)
            duration = max(duration, 0.5)  # minimum 0.5s
            output_path = os.path.join(self.output_dir, f"tts_segment_{i}.mp3")
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            results.append({
                **seg,
                "audio_path": output_path,
                "duration": duration,
            })
        return results


class StubStorage:
    """Stub storage that copies files locally and returns file:// URLs."""

    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = storage_dir
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)

    def upload(self, local_path: str, remote_name: str | None = None) -> str:
        if remote_name is None:
            remote_name = os.path.basename(local_path)
        dest = os.path.join(self.storage_dir, remote_name)
        shutil.copy2(local_path, dest)
        return f"file://{dest}"


# ---------------------------------------------------------------------------
# Fake transcription (since we don't call a real ASR service)
# ---------------------------------------------------------------------------

def fake_transcribe(video_path: str) -> list[dict]:
    """Return fake transcript segments for testing purposes."""
    return [
        {"start": 0.0, "end": 3.5, "text": "Hello and welcome to this video."},
        {"start": 3.5, "end": 7.0, "text": "Today we will learn something new."},
        {"start": 7.0, "end": 11.0, "text": "Let us get started with the lesson."},
        {"start": 11.0, "end": 15.0, "text": "Thank you for watching."},
    ]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(video_url: str, target_lang: str) -> dict:
    """Execute the dubbing pipeline with stub services."""
    job_id = uuid.uuid4().hex[:8]
    work_dir = os.path.join(tempfile.gettempdir(), "asusu", f"seed_test_{job_id}")
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    tts_dir = os.path.join(work_dir, "tts")
    storage_dir = os.path.join(work_dir, "storage")

    print(f"\n{'='*60}")
    print(f"  Asusu Dubbing Pipeline - Seed Test")
    print(f"  Job ID:      {job_id}")
    print(f"  Video:       {video_url}")
    print(f"  Target lang: {target_lang}")
    print(f"  Work dir:    {work_dir}")
    print(f"{'='*60}\n")

    # Step 1: Resolve video source
    print("[Step 1/5] Resolving video source...")
    if video_url.startswith(("http://", "https://")):
        video_path = os.path.join(work_dir, "input_video.mp4")
        print(f"  Downloading {video_url} -> {video_path}")
        try:
            subprocess.run(
                ["curl", "-sL", "-o", video_path, video_url],
                check=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f"  WARNING: Download failed ({exc}). Creating placeholder.")
            # Create a short silent video as placeholder
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=320x240:d=15",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "15",
                "-c:v", "libx264", "-c:a", "aac",
                video_path,
            ], capture_output=True, check=True)
    else:
        video_path = video_url
        if not os.path.isfile(video_path):
            print(f"  Local file not found. Creating placeholder video.")
            video_path = os.path.join(work_dir, "input_video.mp4")
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=320x240:d=15",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "15",
                "-c:v", "libx264", "-c:a", "aac",
                video_path,
            ], capture_output=True, check=True)
    print(f"  Video ready: {video_path}\n")

    # Step 2: Transcribe
    print("[Step 2/5] Transcribing (stubbed)...")
    segments = fake_transcribe(video_path)
    for seg in segments:
        print(f"  [{seg['start']:>5.1f}s - {seg['end']:>5.1f}s] {seg['text']}")
    print()

    # Step 3: Translate
    print("[Step 3/5] Translating...")
    translator = StubTranslator(target_lang)
    translated = translator.translate(segments)
    for seg in translated:
        print(f"  [{seg['start']:>5.1f}s - {seg['end']:>5.1f}s] {seg['translated_text']}")
    print()

    # Step 4: TTS
    print("[Step 4/5] Synthesizing speech (generating silence)...")
    tts = StubTTS(tts_dir)
    audio_segments = tts.synthesize(translated)
    for seg in audio_segments:
        print(f"  Segment {seg['start']:.1f}-{seg['end']:.1f}s -> {seg['audio_path']}")
    print()

    # Step 5: Upload / Storage
    print("[Step 5/5] Uploading to storage (local stub)...")
    storage = StubStorage(storage_dir)
    uploaded_urls = []
    for seg in audio_segments:
        url = storage.upload(seg["audio_path"])
        uploaded_urls.append(url)
        print(f"  Uploaded: {url}")

    # Also upload the original video as the "final output"
    final_url = storage.upload(video_path, f"dubbed_{target_lang}_{os.path.basename(video_path)}")
    print(f"  Final video: {final_url}")
    print()

    # Summary
    result = {
        "job_id": job_id,
        "video_url": video_url,
        "target_lang": target_lang,
        "segments_count": len(segments),
        "translated_segments": len(translated),
        "audio_files": len(audio_segments),
        "uploaded_urls": uploaded_urls,
        "final_video_url": final_url,
        "work_dir": work_dir,
    }

    print(f"{'='*60}")
    print("  Pipeline Complete!")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2))
    print()

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Asusu dubbing pipeline with stub services for testing.",
    )
    parser.add_argument(
        "--video_url",
        type=str,
        default="https://example.com/sample.mp4",
        help="URL or local path to the source video (default: placeholder)",
    )
    parser.add_argument(
        "--target_lang",
        type=str,
        default="es",
        help="Target language code, e.g. es, fr, pt (default: es)",
    )
    args = parser.parse_args()

    # Verify ffmpeg is available
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg is not installed or not on PATH.", file=sys.stderr)
        sys.exit(1)

    run_pipeline(args.video_url, args.target_lang)


if __name__ == "__main__":
    main()
