"""
Renderer API routes.

Endpoints:
  POST /render   — apply a validated edit plan to a landing page.

Returns ``RenderResponse`` on success.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.renderer import (
    RenderRequest,
    RenderResponse,
    RendererErrorResponse,
)
from app.renderer.schemas import RenderInput
from app.renderer.service import RendererService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/renderer",
    tags=["Renderer"],
)

# Module-level service instance — shared across requests.
_service = RendererService()


# ── Render endpoint ────────────────────────────────────────────────────────────


@router.post(
    "/render",
    response_model=RenderResponse,
    responses={
        400: {"model": RendererErrorResponse},
        422: {"model": RendererErrorResponse},
        502: {"model": RendererErrorResponse},
    },
    summary="Render a personalized landing page",
    description=(
        "Apply a validated edit plan to a landing page's HTML, "
        "producing a personalized version with a full audit trail. "
        "Accepts pre-computed outputs of Steps 1–3 "
        "(Ad Agent, Page Agent, Edit Agent)."
    ),
)
async def render_page(body: RenderRequest) -> RenderResponse:
    """
    Render a personalized landing page from an edit plan.

    - **ad_analysis**: Structured ad analysis from Step 1.
    - **page_agent_result**: Combined page structure and analysis from Step 2.
    - **edit_plan**: Structured edit plan from Step 3.

    Returns the personalized HTML page with a complete audit trail.
    """
    # ── Build internal RenderInput ──
    render_input = RenderInput(
        edit_plan=body.edit_plan,
        page_structure=body.page_agent_result.page_structure,
        ad_analysis=body.ad_analysis,
        page_analysis=body.page_agent_result.page_analysis,
    )

    # ── Run rendering ──
    return await _run_render(render_input, body)


# ── Shared execution helper ───────────────────────────────────────────────────


async def _run_render(
    render_input: RenderInput,
    body: RenderRequest,
) -> RenderResponse:
    """
    Execute rendering and wrap the result in an API response.

    Maps internal exceptions to appropriate HTTP error codes.
    """
    try:
        result = await _service.render(render_input)
    except ValueError as exc:
        logger.warning("Render validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Rendering failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Rendering failed: {type(exc).__name__}: {exc}",
        ) from exc

    return RenderResponse(
        url=render_input.page_structure.url,
        personalized_html=result.personalized_html,
        original_html=result.original_html,
        ad_analysis=body.ad_analysis,
        page_analysis=body.page_agent_result.page_analysis,
        edits_applied=result.edits_applied,
        edits_skipped=result.edits_skipped,
        guardrail_result=result.guardrail_result,
        confidence_score=result.confidence_score,
        warnings=result.warnings,
    )
