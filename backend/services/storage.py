"""
Cloud storage using boto3 against Cloudflare R2 (S3-compatible).
"""

import logging
import os
import uuid
from typing import Any, Optional

import boto3
from botocore.config import Config as BotoConfig

from config.settings import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Return a configured boto3 S3 client pointing at Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=BotoConfig(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "adaptive"},
        ),
        region_name="auto",
    )


def upload_video(
    video_path: str,
    job_id: str,
    target_lang: str,
    title: str = "",
) -> dict[str, Any]:
    """
    Upload a dubbed video file to Cloudflare R2.

    The object key follows the pattern::

        dubbed/{job_id}/{target_lang}/{random_hex}.mp4

    Returns a dict with ``url``, ``key``, and ``size_bytes``.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    random_hex = uuid.uuid4().hex[:12]
    key = f"dubbed/{job_id}/{target_lang}/{random_hex}.mp4"

    size_bytes = os.path.getsize(video_path)

    metadata: dict[str, str] = {
        "job_id": job_id,
        "target_lang": target_lang,
    }
    if title:
        metadata["title"] = title

    logger.info(
        "Uploading %s (%.1f MB) to R2 key=%s",
        video_path,
        size_bytes / (1024 * 1024),
        key,
    )

    client = _get_client()
    client.upload_file(
        Filename=video_path,
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        ExtraArgs={
            "ContentType": "video/mp4",
            "Metadata": metadata,
        },
    )

    # Build the public URL
    public_url = settings.R2_PUBLIC_URL.rstrip("/")
    url = f"{public_url}/{key}"

    logger.info("Upload complete: %s (%d bytes)", url, size_bytes)

    return {
        "url": url,
        "key": key,
        "size_bytes": size_bytes,
    }
