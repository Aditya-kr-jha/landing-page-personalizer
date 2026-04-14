"""
Page Agent API routes.

Endpoints:
  POST /analyze   — scrape and analyse a landing page URL (JSON body).

Returns ``AnalyzePageResponse`` on success.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, status

from app.api.schemas.page_agent import (
    AnalyzePageResponse,
    AnalyzePageRequest,
    PageAgentErrorResponse,
)
from app.page_agent.schemas import PageInput
from app.page_agent.service import PageAgentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/page-agent",
    tags=["Page Agent"],
)

# Module-level service instance — shared across requests.
_service = PageAgentService()


# ── Page analysis ──────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=AnalyzePageResponse,
    responses={
        400: {"model": PageAgentErrorResponse},
        422: {"model": PageAgentErrorResponse},
        502: {"model": PageAgentErrorResponse},
    },
    summary="Analyse a landing page",
    description=(
        "Scrape a landing page URL, parse it into labeled sections, "
        "and run an LLM quality assessment."
    ),
)
async def analyze_page(body: AnalyzePageRequest) -> AnalyzePageResponse:
    """
    Scrape and analyse a landing page.

    - **landing_page_url**: Public URL of the landing page to analyse.

    Returns the page structure (sections) and a CRO quality assessment.
    """
    # ── Build internal PageInput ──
    try:
        page_input = PageInput(landing_page_url=str(body.landing_page_url))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # ── Run analysis ──
    return await _run_analysis(page_input)


# ── Shared execution helper ───────────────────────────────────────────────────


async def _run_analysis(page_input: PageInput) -> AnalyzePageResponse:
    """
    Execute page analysis and wrap the result in an API response.

    Maps internal exceptions to appropriate HTTP error codes.
    """
    try:
        result = await _service.analyze(page_input)
    except ValueError as exc:
        logger.warning("Page analysis validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Page scraping failed: %s %s",
            exc.response.status_code,
            exc.request.url,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Failed to fetch landing page: "
                f"HTTP {exc.response.status_code} from {exc.request.url}"
            ),
        ) from exc
    except Exception as exc:
        logger.exception("Page analysis failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Page analysis failed: {type(exc).__name__}: {exc}",
        ) from exc

    return AnalyzePageResponse(
        url=str(page_input.landing_page_url),
        result=result,
    )
