"""
HTTP request / response schemas for the Ad Agent endpoints.

These are the API-facing contracts — separate from the internal
``app.ad_agent.schemas`` which define the agent's data model.

Separation rationale:
  • API schemas handle HTTP concerns (response envelopes, error shapes).
  • Internal schemas define the LLM contract (what the chain returns).
  • The route layer maps between the two.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from app.ad_agent.schemas import AdAnalysis


# ── Requests ───────────────────────────────────────────────────────────────────


class AnalyzeAdURLRequest(BaseModel):
    """
    JSON request body for URL-based ad analysis.

    Provide exactly one of ``ad_image_url`` or ``ad_page_url``.
    For image file uploads, use the ``/upload`` endpoint instead.
    """

    ad_image_url: Optional[HttpUrl] = Field(
        default=None,
        description="Direct URL to the ad image (PNG/JPEG/WebP).",
        examples=["https://example.com/ads/summer-sale.jpg"],
    )
    ad_page_url: Optional[HttpUrl] = Field(
        default=None,
        description=(
            "URL of a page containing the ad "
            "(e.g., Facebook post, Instagram page)."
        ),
        examples=["https://www.facebook.com/ads/library/?id=123456"],
    )


# ── Responses ──────────────────────────────────────────────────────────────────


class AnalyzeAdResponse(BaseModel):
    """
    Successful response from the ad analysis endpoint.

    Wraps the internal ``AdAnalysis`` in an API envelope with metadata.
    """

    status: str = Field(
        default="success",
        description="Request status.",
    )
    input_type: str = Field(
        ...,
        description="Which input path was used (image_upload, image_url, ad_page_url).",
        examples=["image_upload", "image_url", "ad_page_url"],
    )
    analysis: AdAnalysis = Field(
        ...,
        description="Structured ad analysis result.",
    )


class AdAgentErrorResponse(BaseModel):
    """
    Error response from the ad analysis endpoint.

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
