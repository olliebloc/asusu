"""
Main dubbing pipeline orchestrated as a Celery task.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from workers.celery_app import app
from config.settings import settings
from services import downloader, separator, transcriber, translator, tts, mixer, storage

logger = logging.getLogger(__name__)

TOTAL_STEPS = 7


def _progress(task, step: int, message: str) -> None:
    """Update Celery task state with progress metadata."""
    progress = int((step / TOTAL_STEPS) * 100)
    logger.info("Step %d/%d: %s (%d%%)", step, TOTAL_STEPS, message, progress)
    task.update_state(
        state="PROGRESS",
        meta={
            "step": step,
            "total_steps": TOTAL_STEPS,
            "message": message,
            "progress": progress,
        },
    )


@app.task(bind=True, name="workers.pipeline.dub_video")
def dub_video(
    self,
    video_url: Optional[str] = None,
    file_path: Optional[str] = None,
    target_language: str = "es",
    source_language: Optional[str] = None,
    title: Optional[str] = None,
    job_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Full dubbing pipeline.

    Accepts either a *video_url* (downloaded via yt-dlp) or a *file_path*
    (already saved to disk).  Produces a dubbed video in *target_language*
    and uploads it to R2.

    Steps
    -----
    1. Download / locate video
    2. Separate vocals from background
    3. Transcribe vocals
    4. Translate transcript
    5. Generate TTS for translated segments
    6. Mix TTS + background and mux onto video
    7. Upload final video to cloud storage
    """
    if job_id is None:
        job_id = self.request.id or "unknown"

    work_dir = os.path.join(settings.TEMP_DIR, job_id)
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    try:
        # -- Step 1: Acquire video -----------------------------------------------
        _progress(self, 1, "Downloading / loading video")

        if video_url:
            dl_result = downloader.download(video_url, job_id=job_id)
        elif file_path:
            # File was already saved to disk during the upload endpoint
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Uploaded file not found: {file_path}")
            dl_result = {
                "video_path": file_path,
                "title": title or Path(file_path).stem,
                "duration": 0,
                "format": "mp4",
                "job_id": job_id,
            }
        else:
            raise ValueError("Either video_url or file_path must be provided")

        video_path = dl_result["video_path"]
        video_title = title or dl_result.get("title", "untitled")
        video_duration = dl_result.get("duration", 0)

        # -- Step 2: Separate vocals from background -----------------------------
        _progress(self, 2, "Separating vocals from background audio")

        sep_result = separator.separate_from_video(video_path, work_dir)
        vocals_path = sep_result["vocals_path"]
        background_path = sep_result["background_path"]

        # -- Step 3: Transcribe --------------------------------------------------
        _progress(self, 3, "Transcribing speech")

        tx_result = transcriber.transcribe(
            vocals_path,
            language=source_language,
        )
        segments = tx_result["segments"]
        detected_language = tx_result["language"]

        if not segments:
            raise RuntimeError("Transcription produced no segments")

        # Update total_duration from transcription if we didn't get it earlier
        if video_duration == 0 and segments:
            video_duration = max(seg["end"] for seg in segments)

        # -- Step 4: Translate ---------------------------------------------------
        _progress(self, 4, f"Translating {detected_language} -> {target_language}")

        translated_segments = translator.translate_segments(
            segments=segments,
            source_lang=detected_language,
            target_lang=target_language,
            context=f"Video title: {video_title}",
        )

        if not translated_segments:
            raise RuntimeError("Translation produced no segments")

        # -- Step 5: TTS ---------------------------------------------------------
        _progress(self, 5, "Generating dubbed speech audio")

        tts_dir = os.path.join(work_dir, "tts")
        tts_segments = tts.generate_all_segments(
            translated_segments=translated_segments,
            target_lang=target_language,
            output_dir=tts_dir,
        )

        if not tts_segments:
            raise RuntimeError("TTS generation produced no audio segments")

        # -- Step 6: Mix and mux -------------------------------------------------
        _progress(self, 6, "Mixing audio and assembling final video")

        dubbed_audio_path = os.path.join(work_dir, "dubbed_audio.m4a")
        mixer.assemble_dubbed_audio(
            tts_segments=tts_segments,
            background_audio_path=background_path,
            total_duration=video_duration,
            output_path=dubbed_audio_path,
        )

        output_video_path = os.path.join(work_dir, "dubbed_output.mp4")
        mixer.mux_video(
            original_video_path=video_path,
            dubbed_audio_path=dubbed_audio_path,
            output_path=output_video_path,
        )

        # -- Step 7: Upload to R2 ------------------------------------------------
        _progress(self, 7, "Uploading dubbed video")

        upload_result = storage.upload_video(
            video_path=output_video_path,
            job_id=job_id,
            target_lang=target_language,
            title=video_title,
        )

        logger.info("Pipeline complete for job %s", job_id)

        return {
            "status": "completed",
            "url": upload_result["url"],
            "job_id": job_id,
            "target_lang": target_language,
            "title": video_title,
            "duration": video_duration,
            "segments_count": len(tts_segments),
            "size_bytes": upload_result["size_bytes"],
        }

    except Exception:
        logger.exception("Pipeline failed for job %s", job_id)
        raise

    finally:
        # Clean up working directory if configured
        cleanup = os.getenv("CLEANUP_TEMP", "true").lower() in ("true", "1", "yes")
        if cleanup and os.path.isdir(work_dir):
            try:
                shutil.rmtree(work_dir)
                logger.info("Cleaned up work dir: %s", work_dir)
            except OSError:
                logger.warning("Failed to clean up work dir: %s", work_dir, exc_info=True)
