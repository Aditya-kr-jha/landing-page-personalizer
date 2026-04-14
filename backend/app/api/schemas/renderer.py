"""
HTTP request / response schemas for the Renderer endpoints.

These are the API-facing contracts — separate from the internal
``app.renderer.schemas`` which define the renderer's data model.

Separation rationale:
  • API schemas handle HTTP concerns (response envelopes, error shapes).
  • Internal schemas define the pipeline contract (what the service returns).
  • The route layer maps between the two.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.ad_agent.schemas import AdAnalysis
from app.edit_agent.schemas import EditPlan
from app.page_agent.schemas import PageAgentResult, PageAnalysis
from app.renderer.schemas import AppliedEdit, GuardrailResult, SkippedEdit


# ── Requests ───────────────────────────────────────────────────────────────────


class RenderRequest(BaseModel):
    """
    JSON request body for the renderer endpoint.

    Accepts the outputs of Steps 1–3 as pre-computed inputs.
    The orchestrator (or a test client) provides these.
    """

    ad_analysis: AdAnalysis = Field(
        ...,
        description="Structured ad analysis from Step 1 (Ad Agent).",
    )
    page_agent_result: PageAgentResult = Field(
        ...,
        description=(
            "Combined page structure and quality analysis from Step 2 "
            "(Page Agent)."
        ),
    )
    edit_plan: EditPlan = Field(
        ...,
        description="Structured edit plan from Step 3 (Edit Agent).",
    )


# ── Responses ──────────────────────────────────────────────────────────────────


class RenderResponse(BaseModel):
    """
    Successful response from the renderer endpoint.

    This is the **final API response contract** for the full pipeline.
    Contains the personalized HTML page plus a complete audit trail.
    """

    status: str = Field(
        default="success",
        description="Request status.",
    )
    url: str = Field(
        ...,
        description="The landing page URL that was personalized.",
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

    # ── Upstream context ────────────────────────────────────────────────

    ad_analysis: AdAnalysis = Field(
        ...,
        description="The ad analysis from Step 1 (passed through).",
    )
    page_analysis: PageAnalysis = Field(
        ...,
        description="The page quality analysis from Step 2 (passed through).",
    )

    # ── Edit audit trail ────────────────────────────────────────────────

    edits_applied: list[AppliedEdit] = Field(
        default_factory=list,
        description="Structured list of every change successfully made.",
    )
    edits_skipped: list[SkippedEdit] = Field(
        default_factory=list,
        description="Edits that could not be applied, with reasons.",
    )

    # ── Guardrails ──────────────────────────────────────────────────────

    guardrail_result: GuardrailResult = Field(
        ...,
        description="Full guardrail validation report.",
    )

    # ── Metadata ────────────────────────────────────────────────────────

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall personalization quality score (0–1).",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable summary warnings.",
    )


class RendererErrorResponse(BaseModel):
    """
    Error response from the renderer endpoint.

    Returned for validation errors or rendering failures.
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
