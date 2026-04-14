"""
HTTP schemas for the primary End-to-End Personalize API endpoint.

Explicit separation of API layers from domain layers, guaranteeing
stable external contracts. Outputs follow the RenderResponse design exactly.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, HttpUrl, Field

from app.ad_agent.schemas import AdAnalysis, AdInput
from app.page_agent.schemas import PageAnalysis
from app.renderer.schemas import AppliedEdit, GuardrailResult, SkippedEdit


# ── Requests ───────────────────────────────────────────────────────────────────


class PersonalizeRequest(BaseModel):
    """
    JSON request body containing the minimum required information to kick off
    an end-to-end personalization task. Requires exactly one ad designator and
    one landing page URL.
    """

    ad_input: AdInput = Field(
        ...,
        description="Information about the ad (image base64, external URL, or page).",
    )
    landing_page_url: HttpUrl = Field(
        ...,
        description="Public URL of the landing page to personalize.",
    )


# ── Responses ──────────────────────────────────────────────────────────────────


class PersonalizeResponse(BaseModel):
    """
    Successful end-to-end personalization result. Fully hydrates the final
    RenderResponse data so the front-end can display original/modified HTML,
    the model's reasoning, and the exact string manipulations applied.
    """

    status: str = Field(
        default="success",
        description="Request status.",
    )
    url: str = Field(
        ...,
        description="The landing page URL that was correctly personalized.",
    )

    # ── HTML ────────────────────────────────────────────────────────────

    personalized_html: str = Field(
        ...,
        description="The full modified HTML page, ready to serve.",
    )
    original_html: str = Field(
        ...,
        description="The original unmodified HTML page.",
    )

    # ── Upstream Context ────────────────────────────────────────────────

    ad_analysis: AdAnalysis = Field(
        ...,
        description="The generated contextual understanding of the target Ad.",
    )
    page_analysis: PageAnalysis = Field(
        ...,
        description="The generated quality analysis of the initial landing page.",
    )

    # ── Edit Audit Trail ────────────────────────────────────────────────

    edits_applied: list[AppliedEdit] = Field(
        default_factory=list,
        description="Structured list of every change successfully completely injected into DOM.",
    )
    edits_skipped: list[SkippedEdit] = Field(
        default_factory=list,
        description="Edits that failed injection against the HTML or failed safety rules.",
    )

    # ── Guardrails ──────────────────────────────────────────────────────

    guardrail_result: GuardrailResult = Field(
        ...,
        description="Full guardrail validation checking structural safety of outputs.",
    )

    # ── Metadata ────────────────────────────────────────────────────────

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence spanning ad relevancy, layout retention, and copy adjustments.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable warning notifications.",
    )


class PersonalizeErrorResponse(BaseModel):
    """
    Error response for end-to-end failures (Step 1, 2, 3, or 4).
    """

    status: str = Field(
        default="error",
        description="Request error status.",
    )
    error: str = Field(
        ...,
        description="Human-readable summary of what step interrupted execution.",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed server exception dump for trace.",
    )
