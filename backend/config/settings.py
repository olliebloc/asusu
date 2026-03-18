"""
Application settings loaded from environment variables.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration for the Asusu dubbing pipeline."""

    def __init__(self) -> None:
        # API keys
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")

        # Cloudflare R2 / S3-compatible storage
        self.R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
        self.R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
        self.R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "asusu-videos")
        self.R2_ENDPOINT_URL: str = os.getenv("R2_ENDPOINT_URL", "")
        self.R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")

        # Redis / Celery
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Processing limits
        self.MAX_VIDEO_DURATION_MINUTES: int = int(
            os.getenv("MAX_VIDEO_DURATION_MINUTES", "60")
        )
        self.MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))

        # Local filesystem paths
        self.TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/asusu")
        self.OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "/tmp/asusu/output")

        # Supported target languages
        self.SUPPORTED_LANGUAGES: dict[str, dict[str, str]] = {
            "es": {"name": "Spanish", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "pt": {"name": "Portuguese", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "fr": {"name": "French", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "de": {"name": "German", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "zh": {"name": "Mandarin", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "ja": {"name": "Japanese", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "th": {"name": "Thai", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "hi": {"name": "Hindi", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "ar": {"name": "Arabic", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "yo": {"name": "Yoruba", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "ig": {"name": "Igbo", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "sw": {"name": "Swahili", "voice_id": "pNInz6obpgDQGcFmaJgB"},
            "ko": {"name": "Korean", "voice_id": "pNInz6obpgDQGcFmaJgB"},
        }

    def validate(self) -> list[str]:
        """Return a list of configuration problems (empty means all good)."""
        errors: list[str] = []

        if not self.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set")
        if not self.ELEVENLABS_API_KEY:
            errors.append("ELEVENLABS_API_KEY is not set")
        if not self.R2_ACCESS_KEY_ID:
            errors.append("R2_ACCESS_KEY_ID is not set")
        if not self.R2_SECRET_ACCESS_KEY:
            errors.append("R2_SECRET_ACCESS_KEY is not set")
        if not self.R2_ENDPOINT_URL:
            errors.append("R2_ENDPOINT_URL is not set")
        if not self.R2_PUBLIC_URL:
            errors.append("R2_PUBLIC_URL is not set")

        # Ensure temp directories exist
        for dir_path in (self.TEMP_DIR, self.OUTPUT_DIR):
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        return errors


settings = Settings()
