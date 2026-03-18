"""
Video downloading (yt-dlp) and uploaded-file handling.
"""

import json
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Optional

from config.settings import settings

logger = logging.getLogger(__name__)


def _get_duration_ffprobe(file_path: str) -> float:
    """Return the duration in seconds of a media file using ffprobe."""
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


def download(url: str, job_id: Optional[str] = None) -> dict[str, Any]:
    """
    Download a video from *url* using yt-dlp.

    Returns a dict with video_path, title, duration, format and job_id.
    """
    if job_id is None:
        job_id = uuid.uuid4().hex

    work_dir = os.path.join(settings.TEMP_DIR, job_id)
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    # --- Fetch metadata first ------------------------------------------------
    logger.info("Fetching video info for %s", url)
    info_cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        url,
    ]
    info_result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
    info = json.loads(info_result.stdout)

    title: str = info.get("title", "untitled")
    duration: float = float(info.get("duration", 0))

    # Enforce duration limit
    max_seconds = settings.MAX_VIDEO_DURATION_MINUTES * 60
    if duration > max_seconds:
        raise ValueError(
            f"Video is {duration / 60:.1f} min, exceeding the "
            f"{settings.MAX_VIDEO_DURATION_MINUTES} min limit"
        )

    # --- Download the video ---------------------------------------------------
    output_template = os.path.join(work_dir, "%(id)s.%(ext)s")
    dl_cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", output_template,
        url,
    ]
    logger.info("Downloading video: %s", title)
    subprocess.run(dl_cmd, capture_output=True, text=True, check=True)

    # Find the downloaded file
    video_path: Optional[str] = None
    for fname in os.listdir(work_dir):
        if fname.endswith(".mp4"):
            video_path = os.path.join(work_dir, fname)
            break

    if video_path is None:
        raise FileNotFoundError("yt-dlp did not produce an mp4 file")

    # Re-read actual duration from file if metadata was missing
    if duration == 0:
        duration = _get_duration_ffprobe(video_path)

    logger.info("Downloaded %s (%.1fs) -> %s", title, duration, video_path)

    return {
        "video_path": video_path,
        "title": title,
        "duration": duration,
        "format": "mp4",
        "job_id": job_id,
    }


def save_upload(
    file_content: bytes,
    filename: str,
    job_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Persist raw uploaded bytes and return the same metadata dict as download().
    """
    if job_id is None:
        job_id = uuid.uuid4().hex

    work_dir = os.path.join(settings.TEMP_DIR, job_id)
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    # Enforce size limit
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise ValueError(
            f"Upload is {size_mb:.1f} MB, exceeding the "
            f"{settings.MAX_UPLOAD_SIZE_MB} MB limit"
        )

    # Save to disk
    safe_name = "".join(
        c if c.isalnum() or c in (".", "-", "_") else "_" for c in filename
    )
    video_path = os.path.join(work_dir, safe_name)
    with open(video_path, "wb") as f:
        f.write(file_content)

    # Get duration via ffprobe
    duration = _get_duration_ffprobe(video_path)
    max_seconds = settings.MAX_VIDEO_DURATION_MINUTES * 60
    if duration > max_seconds:
        os.remove(video_path)
        raise ValueError(
            f"Video is {duration / 60:.1f} min, exceeding the "
            f"{settings.MAX_VIDEO_DURATION_MINUTES} min limit"
        )

    title = Path(filename).stem

    logger.info("Saved upload %s (%.1fs) -> %s", title, duration, video_path)

    return {
        "video_path": video_path,
        "title": title,
        "duration": duration,
        "format": Path(filename).suffix.lstrip(".") or "mp4",
        "job_id": job_id,
    }
