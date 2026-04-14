"""
HTTP request / response schemas for the Edit Agent endpoints.

These are the API-facing contracts — separate from the internal
``app.edit_agent.schemas`` which define the agent's data model.

Separation rationale:
  • API schemas handle HTTP concerns (response envelopes, error shapes).
  • Internal schemas define the LLM contract (what the chain returns).
  • The route layer maps between the two.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.ad_agent.schemas import AdAnalysis
from app.edit_agent.schemas import EditPlan
from app.page_agent.schemas import PageAgentResult


# ── Requests ───────────────────────────────────────────────────────────────────


class GenerateEditsRequest(BaseModel):
    """
    JSON request body for edit generation.

    Accepts the outputs of Steps 1 and 2 as pre-computed inputs.
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


# ── Responses ──────────────────────────────────────────────────────────────────


class GenerateEditsResponse(BaseModel):
    """
    Successful response from the edit generation endpoint.

    Wraps the internal ``EditPlan`` in an API envelope with metadata.
    """

    status: str = Field(
        default="success",
        description="Request status.",
    )
    url: str = Field(
        ...,
        description="The landing page URL the edits target.",
    )
    edit_plan: EditPlan = Field(
        ...,
        description="Structured edit plan with per-section replacements.",
    )


class EditAgentErrorResponse(BaseModel):
    """
    Error response from the edit generation endpoint.

    Returned for validation errors or LLM failures.
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
