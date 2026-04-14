"""
Ad Agent API routes.

Endpoints:
  POST /analyze/url      — analyse an ad via image URL or ad page URL (JSON body).
  POST /analyze/upload   — analyse an ad via image file upload (multipart).

Both endpoints return ``AnalyzeAdResponse`` on success.
"""

from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.ad_agent.schemas import AdInput
from app.ad_agent.service import AdAgentService
from app.api.schemas.ad_agent import (
    AdAgentErrorResponse,
    AnalyzeAdResponse,
    AnalyzeAdURLRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ad-agent",
    tags=["Ad Agent"],
)

# Module-level service instance — shared across requests.
_service = AdAgentService()


# ── URL-based analysis ─────────────────────────────────────────────────────────


@router.post(
    "/analyze/url",
    response_model=AnalyzeAdResponse,
    responses={
        400: {"model": AdAgentErrorResponse},
        422: {"model": AdAgentErrorResponse},
        502: {"model": AdAgentErrorResponse},
    },
    summary="Analyze ad via URL",
    description=(
        "Analyze an ad creative by providing either an image URL or an ad page "
        "URL. Exactly one must be provided."
    ),
)
async def analyze_ad_url(body: AnalyzeAdURLRequest) -> AnalyzeAdResponse:
    """
    Analyse an ad via image URL or ad page URL.

    - **ad_image_url**: Direct link to the ad image (PNG/JPEG/WebP).
    - **ad_page_url**: URL of a page containing the ad (scraped for text).

    Provide exactly one.
    """
    # ── Validate exactly one URL provided ──
    has_image = body.ad_image_url is not None
    has_page = body.ad_page_url is not None

    if has_image == has_page:  # both True or both False
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Provide exactly one of 'ad_image_url' or 'ad_page_url', "
                "not both or neither."
            ),
        )

    # ── Build internal AdInput ──
    try:
        ad_input = AdInput(
            ad_image_url=str(body.ad_image_url) if has_image else None,
            ad_page_url=str(body.ad_page_url) if has_page else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # ── Run analysis ──
    return await _run_analysis(ad_input)


# ── Upload-based analysis ─────────────────────────────────────────────────────


@router.post(
    "/analyze/upload",
    response_model=AnalyzeAdResponse,
    responses={
        400: {"model": AdAgentErrorResponse},
        502: {"model": AdAgentErrorResponse},
    },
    summary="Analyze ad via image upload",
    description="Upload an ad creative image (PNG/JPEG/WebP) for analysis.",
)
async def analyze_ad_upload(
    file: UploadFile = File(
        ...,
        description="Ad creative image file (PNG, JPEG, or WebP).",
    ),
) -> AnalyzeAdResponse:
    """
    Analyse an uploaded ad creative image.

    Accepts PNG, JPEG, or WebP. Max recommended size: 10 MB.
    """
    # ── Validate content type ──
    allowed_types = {"image/png", "image/jpeg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type: {file.content_type}. "
                f"Allowed: {', '.join(sorted(allowed_types))}"
            ),
        )

    # ── Read and encode ──
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    b64_encoded = base64.b64encode(contents).decode("utf-8")
    data_uri = f"data:{file.content_type};base64,{b64_encoded}"

    # ── Build internal AdInput ──
    ad_input = AdInput(ad_image_base64=data_uri)

    # ── Run analysis ──
    return await _run_analysis(ad_input)


# ── Shared execution helper ───────────────────────────────────────────────────


async def _run_analysis(ad_input: AdInput) -> AnalyzeAdResponse:
    """
    Execute ad analysis and wrap the result in an API response.

    Maps internal exceptions to appropriate HTTP error codes.
    """
    try:
        analysis = await _service.analyze(ad_input)
    except ValueError as exc:
        logger.warning("Ad analysis validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Ad analysis failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ad analysis failed: {type(exc).__name__}: {exc}",
        ) from exc

    return AnalyzeAdResponse(
        input_type=ad_input.input_type.value,
        analysis=analysis,
    )
