"""
HTTP request / response schemas for the Page Agent endpoints.

These are the API-facing contracts — separate from the internal
``app.page_agent.schemas`` which define the agent's data model.

Separation rationale:
  • API schemas handle HTTP concerns (response envelopes, error shapes).
  • Internal schemas define the LLM contract (what the chain returns).
  • The route layer maps between the two.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from app.page_agent.schemas import PageAgentResult


# ── Requests ───────────────────────────────────────────────────────────────────


class AnalyzePageRequest(BaseModel):
    """
    JSON request body for landing page analysis.

    Provide the URL of the landing page to scrape and analyse.
    """

    landing_page_url: HttpUrl = Field(
        ...,
        description="Public URL of the landing page to scrape and analyse.",
        examples=["https://example.com/landing-page"],
    )


# ── Responses ──────────────────────────────────────────────────────────────────


class AnalyzePageResponse(BaseModel):
    """
    Successful response from the page analysis endpoint.

    Wraps the internal ``PageAgentResult`` in an API envelope with metadata.
    """

    status: str = Field(
        default="success",
        description="Request status.",
    )
    url: str = Field(
        ...,
        description="The landing page URL that was analysed.",
    )
    result: PageAgentResult = Field(
        ...,
        description="Combined page structure and quality analysis.",
    )


class PageAgentErrorResponse(BaseModel):
    """
    Error response from the page analysis endpoint.

    Returned for validation errors, scraping failures, or LLM errors.
    """

    status: str = Field(
        default="error",
        description="Request status.",
    )
    error: str = Field(
        ...,
        description="Human-readable error message.",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Additional error context (e.g., traceback hint).",
    )
