"""
Data contracts for the Renderer pipeline step (Step 4).

RenderInput      — bundles EditPlan + PageStructure (+ optional context).
AppliedEdit      — one successfully applied text replacement.
SkippedEdit      — one edit that could not be applied.
GuardrailWarning — a single guardrail warning with severity.
GuardrailResult  — aggregated result of all pre-render validation checks.
RenderResult     — final output: modified HTML + full audit trail.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.ad_agent.schemas import AdAnalysis
from app.edit_agent.schemas import EditPlan, EditType
from app.page_agent.schemas import PageAnalysis, PageStructure


# ── Enums ──────────────────────────────────────────────────────────────────────


class MatchType(str, Enum):
    """How the original text was located in the DOM."""

    EXACT = "exact"
    FUZZY = "fuzzy"


class GuardrailSeverity(str, Enum):
    """Severity level for a guardrail warning."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class GuardrailCheckName(str, Enum):
    """Names of the individual guardrail checks."""

    FACT_CHECK = "fact_check"
    SCOPE_CHECK = "scope_check"
    SCHEMA_CHECK = "schema_check"
    HTML_SAFETY_CHECK = "html_safety_check"


# ── Input ──────────────────────────────────────────────────────────────────────


class RenderInput(BaseModel):
    """
    Composite input for the Renderer.

    Bundles the EditPlan with the page data needed to apply edits.
    The orchestrator builds this from the results of Steps 1–3.
    """

    edit_plan: EditPlan = Field(
        ...,
        description="Structured edit plan from Step 3 (Edit Agent).",
    )
    page_structure: PageStructure = Field(
        ...,
        description="Scraped HTML and labeled sections from Step 2 (Page Agent).",
    )
    ad_analysis: AdAnalysis = Field(
        ...,
        description="Structured ad analysis from Step 1 (Ad Agent).",
    )
    page_analysis: PageAnalysis = Field(
        ...,
        description="LLM quality assessment from Step 2 (Page Agent).",
    )


# ── Guardrail outputs ─────────────────────────────────────────────────────────


class GuardrailWarning(BaseModel):
    """A single warning raised by a guardrail check."""

    check_name: GuardrailCheckName = Field(
        ...,
        description="Which guardrail check raised this warning.",
    )
    severity: GuardrailSeverity = Field(
        ...,
        description="Severity level of this warning.",
    )
    section_id: Optional[str] = Field(
        default=None,
        description="The section the warning relates to, if applicable.",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the issue.",
    )


class GuardrailCheckResult(BaseModel):
    """Result of a single guardrail check."""

    check_name: GuardrailCheckName = Field(
        ...,
        description="Name of the check.",
    )
    passed: bool = Field(
        ...,
        description="Whether this check passed overall.",
    )
    warnings: list[GuardrailWarning] = Field(
        default_factory=list,
        description="Warnings raised during this check.",
    )
    blocked_section_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Section IDs whose edits were blocked by this check. "
            "These edits will be removed from the plan before rendering."
        ),
    )


class GuardrailResult(BaseModel):
    """Aggregated result of all pre-render guardrail checks."""

    overall_passed: bool = Field(
        ...,
        description="True if all critical checks passed (rendering can proceed).",
    )
    checks: list[GuardrailCheckResult] = Field(
        default_factory=list,
        description="Individual results for each guardrail check.",
    )
    all_warnings: list[GuardrailWarning] = Field(
        default_factory=list,
        description="Flattened list of all warnings across checks.",
    )
    blocked_section_ids: list[str] = Field(
        default_factory=list,
        description="Union of all section IDs blocked by any guardrail.",
    )


# ── Render outputs ─────────────────────────────────────────────────────────────


class AppliedEdit(BaseModel):
    """One successfully applied text replacement."""

    section_id: str = Field(
        ...,
        description="The section this edit was applied to.",
    )
    edit_type: EditType = Field(
        ...,
        description="Category of edit applied.",
    )
    original_text: str = Field(
        ...,
        description="The original text that was replaced.",
    )
    replacement_text: str = Field(
        ...,
        description="The new text that was inserted.",
    )
    match_type: MatchType = Field(
        ...,
        description="Whether the match was exact or fuzzy.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this individual edit (from Step 3).",
    )


class SkippedEdit(BaseModel):
    """One edit that could not be applied."""

    section_id: str = Field(
        ...,
        description="The section this edit targeted.",
    )
    edit_type: EditType = Field(
        ...,
        description="Category of edit that was skipped.",
    )
    reason: str = Field(
        ...,
        description=(
            "Why the edit was skipped — e.g., 'no text match found', "
            "'blocked by fact_check guardrail', 'section not found in DOM'."
        ),
    )


class RenderResult(BaseModel):
    """
    Final output of the Renderer pipeline step.

    Contains the modified HTML page plus a complete audit trail
    of every edit applied, skipped, and every warning raised.
    """

    # ── HTML ────────────────────────────────────────────────────────────

    personalized_html: str = Field(
        ...,
        description="The full modified HTML page, ready to serve.",
    )
    original_html: str = Field(
        ...,
        description="The original unmodified HTML page.",
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
        description=(
            "Overall confidence in the personalization quality (0–1). "
            "Accounts for edit success rate and guardrail warnings."
        ),
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable summary warnings for the API consumer.",
    )
