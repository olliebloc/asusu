"""
Pydantic models for API request / response validation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """Request body for the /translate endpoint (JSON variant)."""

    video_url: Optional[str] = Field(
        None,
        description="Public URL of the video to dub (YouTube, direct link, etc.).",
    )
    target_languages: list[str] = Field(
        ...,
        min_length=1,
        description="List of ISO 639-1 language codes to dub into.",
    )
    source_language: Optional[str] = Field(
        None,
        description="Source language code. Auto-detected when omitted.",
    )
    title: Optional[str] = Field(
        None,
        description="Optional title for the video (used in metadata and context).",
    )


class TranslateResponse(BaseModel):
    """Response returned after a dubbing job is accepted."""

    job_ids: list[str] = Field(
        ...,
        description="One Celery task ID per target language requested.",
    )
    message: str = Field(
        default="Dubbing jobs enqueued",
        description="Human-readable confirmation.",
    )


class JobStatus(BaseModel):
    """Current status of a dubbing job."""

    job_id: str
    state: str = Field(description="PENDING | PROGRESS | SUCCESS | FAILURE")
    progress: Optional[int] = Field(None, description="0-100 completion percentage")
    step: Optional[int] = None
    total_steps: Optional[int] = None
    message: Optional[str] = None
    result: Optional[dict[str, Any]] = Field(
        None,
        description="Final result payload (only when state=SUCCESS).",
    )
    error: Optional[str] = Field(
        None,
        description="Error description (only when state=FAILURE).",
    )


class LanguageInfo(BaseModel):
    """Metadata for a single supported language."""

    code: str
    name: str
    voice_id: str


class LanguagesResponse(BaseModel):
    """List of supported dubbing target languages."""

    languages: list[LanguageInfo]
