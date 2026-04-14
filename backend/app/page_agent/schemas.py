"""
Data contracts for the Page Agent pipeline step.

PageInput       — what the caller sends (landing page URL).
PageStructure   — scraped HTML + labeled sections (deterministic parse).
PageAnalysis    — LLM quality assessment of each section.
PageAgentResult — combined output returned to the orchestrator.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


# ── Enums ──────────────────────────────────────────────────────────────────────


class SectionType(str, Enum):
    """Semantic type of a parsed landing-page section."""

    HERO = "hero"
    HEADLINE = "headline"
    SUBHEADLINE = "subheadline"
    CTA = "cta"
    BENEFITS = "benefits"
    TESTIMONIALS = "testimonials"
    TRUST_SIGNALS = "trust_signals"
    FEATURES = "features"
    PRICING = "pricing"
    FAQ = "faq"
    FOOTER = "footer"
    NAVIGATION = "navigation"
    OTHER = "other"


# Section types that are structural / non-conversion-relevant.
# The analysis chain skips these to save tokens; Step 3 never rewrites them.
NON_EDITABLE_SECTION_TYPES: frozenset[SectionType] = frozenset({
    SectionType.NAVIGATION,
    SectionType.FOOTER,
})


# ── Input ──────────────────────────────────────────────────────────────────────


class PageInput(BaseModel):
    """
    Landing page input — a single URL to scrape and analyse.

    This is the internal contract used by the service layer.
    """

    landing_page_url: HttpUrl = Field(
        ...,
        description="Public URL of the landing page to scrape and analyse.",
    )


# ── Internal / Domain ─────────────────────────────────────────────────────────


class PageSection(BaseModel):
    """
    One parsed section of a landing page.

    Produced by the deterministic scraper (no LLM involved).
    """

    section_id: str = Field(
        ...,
        description=(
            "Unique identifier for this section "
            "(e.g., 'hero_0', 'benefits_1')."
        ),
    )
    section_type: SectionType = Field(
        ...,
        description="Semantic category of the section.",
    )
    css_selector: str = Field(
        ...,
        description="CSS selector path used to locate this element in the DOM.",
    )
    html_content: str = Field(
        ...,
        description="Raw HTML of the section.",
    )
    text_content: str = Field(
        ...,
        description="Visible text extracted from the section.",
    )


class PageStructure(BaseModel):
    """
    Full scrape result for a landing page.

    Contains the raw HTML plus a list of labeled, parsed sections.
    """

    url: str = Field(
        ...,
        description="The URL that was scraped.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Page <title> tag content.",
    )
    meta_description: Optional[str] = Field(
        default=None,
        description="Content of the <meta name='description'> tag.",
    )
    raw_html: str = Field(
        ...,
        description="Full page HTML as fetched.",
    )
    sections: list[PageSection] = Field(
        default_factory=list,
        description="Labeled sections detected in the page.",
    )


# ── Output — LLM quality assessment ───────────────────────────────────────────


class SectionQualityScore(BaseModel):
    """
    LLM quality assessment for a single page section.

    Used inside ``PageAnalysis.section_scores``.
    """

    section_id: str = Field(
        ...,
        description="References the ``PageSection.section_id`` being scored.",
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How relevant the section content is to the page goal (0–1).",
    )
    clarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How clear and readable the section is (0–1).",
    )
    persuasion_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How persuasive the section is for conversion (0–1).",
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted overall quality score for this section (0–1).",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Identified weaknesses in this section.",
    )
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions to improve this section.",
    )


class PageAnalysis(BaseModel):
    """
    LLM-generated quality assessment of a landing page.

    Produced by the page analysis chain using structured output.
    Consumed by the Edit Agent to decide which sections to rewrite.
    """

    # ── Overall assessment ──────────────────────────────────────────────

    overall_page_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall landing page effectiveness score (0–1).",
    )
    message_clarity: str = Field(
        ...,
        description=(
            "One-paragraph assessment of how clearly the page "
            "communicates its core message."
        ),
    )
    target_audience_alignment: str = Field(
        ...,
        description=(
            "Assessment of how well the page speaks to its "
            "apparent target audience."
        ),
    )
    cta_effectiveness: str = Field(
        ...,
        description="Assessment of call-to-action clarity and persuasiveness.",
    )

    # ── Per-section scores ──────────────────────────────────────────────

    section_scores: list[SectionQualityScore] = Field(
        default_factory=list,
        description="Quality scores for each identified section.",
    )

    # ── Aggregated insights ─────────────────────────────────────────────

    key_weaknesses: list[str] = Field(
        default_factory=list,
        description="Top weaknesses across the entire page.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Prioritised recommendations for improvement.",
    )

    # ── Metadata ────────────────────────────────────────────────────────

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Self-assessed confidence of the analysis (0.0–1.0).",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any caveats or issues encountered during analysis.",
    )


# ── Combined result ────────────────────────────────────────────────────────────


class PageAgentResult(BaseModel):
    """
    Combined output of the Page Agent pipeline step.

    Bundles the deterministic scrape result (``PageStructure``) with the
    LLM quality assessment (``PageAnalysis``) into a single typed object
    for the orchestrator.
    """

    page_structure: PageStructure = Field(
        ...,
        description="Scraped HTML and labeled sections.",
    )
    page_analysis: PageAnalysis = Field(
        ...,
        description="LLM quality assessment of the page.",
    )
