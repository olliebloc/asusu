"""
API route definitions for the Asusu dubbing service.
"""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from api.schemas import (
    JobStatus,
    LanguageInfo,
    LanguagesResponse,
    TranslateRequest,
    TranslateResponse,
)
from config.settings import settings
from services.downloader import save_upload
from workers.pipeline import dub_video

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /translate  (JSON body — URL-based)
# ---------------------------------------------------------------------------

@router.post("/translate", response_model=TranslateResponse)
async def translate(
    request: Request,
    video_file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    target_languages: Optional[str] = Form(None),
    source_language: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
) -> TranslateResponse:
    """
    Accept a video (URL or upload) and enqueue dubbing jobs for each
    requested target language.

    Supports both ``application/json`` and ``multipart/form-data``.
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # Parse JSON body
        body = await request.json()
        req_video_url = body.get("video_url")
        req_target_langs = body.get("target_languages", [])
        req_source_lang = body.get("source_language")
        req_title = body.get("title")
        uploaded_file = None
    else:
        # Multipart form data
        req_video_url = video_url
        uploaded_file = video_file if video_file and video_file.filename else None
        if target_languages:
            # Support both comma-separated and JSON array
            try:
                req_target_langs = json.loads(target_languages)
            except (json.JSONDecodeError, TypeError):
                req_target_langs = [
                    lang.strip() for lang in target_languages.split(",") if lang.strip()
                ]
        else:
            raise HTTPException(status_code=422, detail="target_languages is required")
        req_source_lang = source_language
        req_title = title

    if not req_target_langs:
        raise HTTPException(status_code=422, detail="target_languages is required")

    # Validate target languages
    for lang in req_target_langs:
        if lang not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported target language: {lang}. "
                       f"Supported: {', '.join(sorted(settings.SUPPORTED_LANGUAGES))}",
            )

    # Determine video source
    file_path: Optional[str] = None

    if uploaded_file is not None:
        content = await uploaded_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        job_id_base = uuid.uuid4().hex
        upload_result = save_upload(content, uploaded_file.filename, job_id=job_id_base)
        file_path = upload_result["video_path"]
        if not req_title:
            req_title = upload_result.get("title")
    elif req_video_url:
        pass  # Will be downloaded by the worker
    else:
        raise HTTPException(
            status_code=400,
            detail="Either video_url or a video_file upload is required",
        )

    # Enqueue one task per target language
    job_ids: list[str] = []
    for lang in req_target_langs:
        task = dub_video.apply_async(
            kwargs={
                "video_url": req_video_url if file_path is None else None,
                "file_path": file_path,
                "target_language": lang,
                "source_language": req_source_lang,
                "title": req_title,
            },
        )
        job_ids.append(task.id)
        logger.info("Enqueued dubbing job %s for language %s", task.id, lang)

    return TranslateResponse(
        job_ids=job_ids,
        message=f"Enqueued {len(job_ids)} dubbing job(s)",
    )


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Return the current status of a dubbing job."""
    result = dub_video.AsyncResult(job_id)

    state = result.state or "PENDING"
    meta = result.info if isinstance(result.info, dict) else {}

    if state == "PROGRESS":
        return JobStatus(
            job_id=job_id,
            state=state,
            progress=meta.get("progress"),
            step=meta.get("step"),
            total_steps=meta.get("total_steps"),
            message=meta.get("message"),
        )
    elif state == "SUCCESS":
        result_data = result.result if isinstance(result.result, dict) else meta
        return JobStatus(
            job_id=job_id,
            state=state,
            progress=100,
            step=7,
            total_steps=7,
            message="Dubbing complete",
            result=result_data,
        )
    elif state == "FAILURE":
        error_str = str(result.info) if result.info else "Unknown error"
        return JobStatus(
            job_id=job_id,
            state=state,
            error=error_str,
        )
    else:
        # PENDING or other states
        return JobStatus(
            job_id=job_id,
            state=state,
            message="Job is waiting to be picked up by a worker",
        )


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/result
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str) -> dict:
    """Return the final result of a completed dubbing job."""
    result = dub_video.AsyncResult(job_id)

    if result.state == "SUCCESS":
        return result.result  # type: ignore[return-value]
    elif result.state == "FAILURE":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {result.info}",
        )
    else:
        raise HTTPException(
            status_code=202,
            detail=f"Job is not complete yet (state={result.state})",
        )


# ---------------------------------------------------------------------------
# GET /languages
# ---------------------------------------------------------------------------

@router.get("/languages", response_model=LanguagesResponse)
async def list_languages() -> LanguagesResponse:
    """Return all supported dubbing target languages."""
    languages = [
        LanguageInfo(
            code=code,
            name=info["name"],
            voice_id=info["voice_id"],
        )
        for code, info in sorted(settings.SUPPORTED_LANGUAGES.items())
    ]
    return LanguagesResponse(languages=languages)
