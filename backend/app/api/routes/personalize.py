"""
End-to-End Personalization API routes.

Endpoints:
  POST /personalize — run ad analysis, page structure scraping, editing, and rendering.

Delegates logic-free operation entirely to the `PipelineOrchestrator`. Uses dependency
injection to guarantee modular testability and concurrency management.
"""

from __future__ import annotations

import logging
import os
import base64
from pathlib import Path
from typing import Annotated, Optional

from pydantic import HttpUrl
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile

from app.ad_agent import AdInput
from app.api.schemas.personalize import (
    PersonalizeErrorResponse,
    PersonalizeRequest,
    PersonalizeResponse,
)
from app.page_agent.schemas import PageInput
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.schemas import PipelineInput

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/personalize",
    tags=["End-to-End Pipeline"],
)


# ── Dependencies ───────────────────────────────────────────────────────────────


def get_pipeline_orchestrator() -> PipelineOrchestrator:
    """Dependency injector establishing singleton-like orchestration service."""
    return PipelineOrchestrator()


OrchestratorDep = Annotated[PipelineOrchestrator, Depends(get_pipeline_orchestrator)]


# ── Personalize Endpoint ───────────────────────────────────────────────────────


@router.post(
    "",
    response_model=PersonalizeResponse,
    responses={
        400: {"model": PersonalizeErrorResponse},
        422: {"model": PersonalizeErrorResponse},
        502: {"model": PersonalizeErrorResponse},
    },
    summary="End-to-End Personalization Execution",
    description=(
        "Executes the entire Ad-to-Landing Page pipeline. Parallelizes Ad image/url "
        "scanning and webpage scraping/scoring before intelligently altering the DOM structure."
    ),
)
async def run_personalization_pipeline(
    body: PersonalizeRequest,
    orchestrator: OrchestratorDep,
) -> PersonalizeResponse:
    """
    Coordinate and execute all four independent microservices using a JSON payload.
    """
    logger.info("Handling E2E personalization for %s", body.landing_page_url)

    pipeline_input = PipelineInput(
        ad_input=body.ad_input,
        page_input=PageInput(landing_page_url=body.landing_page_url),
    )

    return await _execute_pipeline(
        pipeline_input=pipeline_input,
        landing_page_url=str(body.landing_page_url),
        orchestrator=orchestrator,
    )


@router.post(
    "/upload",
    response_model=PersonalizeResponse,
    responses={
        400: {"model": PersonalizeErrorResponse},
        422: {"model": PersonalizeErrorResponse},
        502: {"model": PersonalizeErrorResponse},
    },
    summary="End-to-End Personalization (File Upload)",
    description=(
        "Alternative endpoint accepting multipart/form-data. "
        "Allows direct image file uploads from Swagger UI or standard web forms."
    ),
)
async def run_personalization_upload(
    orchestrator: OrchestratorDep,
    landing_page_url: HttpUrl = Form(
        ..., description="Public URL of the landing page to personalize."
    ),
    ad_image: Optional[UploadFile] = File(None, description="Image file upload."),
    ad_image_url: Optional[HttpUrl] = Form(
        None, description="Public URL of the ad image."
    ),
    ad_page_url: Optional[HttpUrl] = Form(
        None, description="Public URL of the ad target page."
    ),
) -> PersonalizeResponse:
    """
    Multipart wrapper over the standard pipeline. Reads uploaded file into base64.
    """
    logger.info("Handling E2E personalization (via Upload) for %s", landing_page_url)

    ad_input_kwargs = {}
    if ad_image and ad_image.filename:
        image_bytes = await ad_image.read()
        ad_input_kwargs["ad_image_base64"] = base64.b64encode(image_bytes).decode("utf-8")
    elif ad_image_url:
        ad_input_kwargs["ad_image_url"] = str(ad_image_url)
    elif ad_page_url:
        ad_input_kwargs["ad_page_url"] = str(ad_page_url)
    else:
        raise HTTPException(
            status_code=400,
            detail="You must provide either an ad_image file, an ad_image_url, or an ad_page_url."
        )

    try:
        ad_input = AdInput(**ad_input_kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    pipeline_input = PipelineInput(
        ad_input=ad_input,
        page_input=PageInput(landing_page_url=landing_page_url),
    )

    return await _execute_pipeline(
        pipeline_input=pipeline_input,
        landing_page_url=str(landing_page_url),
        orchestrator=orchestrator,
    )


# ── Shared Execution Logic ─────────────────────────────────────────────────────


async def _execute_pipeline(
    pipeline_input: PipelineInput,
    landing_page_url: str,
    orchestrator: PipelineOrchestrator,
) -> PersonalizeResponse:
    """Consolidated pipeline logic shared by both JSON and Multi-part endpoints."""
    try:
        pipeline_result = await orchestrator.run(pipeline_input)
    except ValueError as exc:
        logger.warning("Pipeline validation exception: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("E2E Pipeline crashed critically and could not recover.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Downstream service error during execution: {type(exc).__name__}: {str(exc)}",
        ) from exc

    render_result = pipeline_result.render_result

    # ── Dev/Testing Convenience: Save HTML to disk ──
    output_dir = Path(__file__).resolve().parent.parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    orig_path = output_dir / "original.html"
    pers_path = output_dir / "personalized.html"

    with open(orig_path, "w", encoding="utf-8") as f:
        f.write(render_result.original_html)
    with open(pers_path, "w", encoding="utf-8") as f:
        f.write(render_result.personalized_html)

    logger.info("Saved original and personalized HTML to %s", output_dir)

    return PersonalizeResponse(
        url=landing_page_url,
        personalized_html=render_result.personalized_html,
        original_html=render_result.original_html,
        ad_analysis=pipeline_result.ad_analysis,
        page_analysis=pipeline_result.page_analysis,
        edits_applied=render_result.edits_applied,
        edits_skipped=render_result.edits_skipped,
        guardrail_result=render_result.guardrail_result,
        confidence_score=render_result.confidence_score,
        warnings=render_result.warnings,
    )
