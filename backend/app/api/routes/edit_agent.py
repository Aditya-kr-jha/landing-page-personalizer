"""
Edit Agent API routes.

Endpoints:
  POST /generate   — generate an edit plan from ad analysis + page data.

Returns ``GenerateEditsResponse`` on success.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.edit_agent import (
    EditAgentErrorResponse,
    GenerateEditsRequest,
    GenerateEditsResponse,
)
from app.edit_agent.schemas import EditInput
from app.edit_agent.service import EditAgentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/edit-agent",
    tags=["Edit Agent"],
)

# Module-level service instance — shared across requests.
_service = EditAgentService()


# ── Edit generation ────────────────────────────────────────────────────────────


@router.post(
    "/generate",
    response_model=GenerateEditsResponse,
    responses={
        400: {"model": EditAgentErrorResponse},
        422: {"model": EditAgentErrorResponse},
        502: {"model": EditAgentErrorResponse},
    },
    summary="Generate an edit plan",
    description=(
        "Generate a structured edit plan that aligns a landing page "
        "with an ad creative's messaging.  Accepts the pre-computed "
        "outputs of Steps 1 (Ad Agent) and 2 (Page Agent)."
    ),
)
async def generate_edits(body: GenerateEditsRequest) -> GenerateEditsResponse:
    """
    Generate an edit plan from ad analysis + page data.

    - **ad_analysis**: Structured ad analysis from Step 1.
    - **page_agent_result**: Combined page structure and analysis from Step 2.

    Returns a structured edit plan with per-section text replacements.
    """
    # ── Build internal EditInput ──
    edit_input = EditInput(
        ad_analysis=body.ad_analysis,
        page_structure=body.page_agent_result.page_structure,
        page_analysis=body.page_agent_result.page_analysis,
    )

    # ── Run generation ──
    return await _run_generation(edit_input)


# ── Shared execution helper ───────────────────────────────────────────────────


async def _run_generation(edit_input: EditInput) -> GenerateEditsResponse:
    """
    Execute edit generation and wrap the result in an API response.

    Maps internal exceptions to appropriate HTTP error codes.
    """
    try:
        edit_plan = await _service.generate(edit_input)
    except ValueError as exc:
        logger.warning("Edit generation validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Edit generation failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Edit generation failed: {type(exc).__name__}: {exc}",
        ) from exc

    return GenerateEditsResponse(
        url=edit_input.page_structure.url,
        edit_plan=edit_plan,
    )
