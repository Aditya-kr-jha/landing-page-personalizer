"""
Data contracts for the Ad Agent pipeline step.

AdInput   — what the caller sends (image bytes, image URL, or ad page URL).
AdAnalysis — structured extraction of ad messaging signals.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator


# ── Enums ──────────────────────────────────────────────────────────────────────


class AdTone(str, Enum):
    """Perceived emotional tone of the ad creative."""

    URGENT = "urgent"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    LUXURIOUS = "luxurious"
    INSPIRATIONAL = "inspirational"
    FEARFUL = "fearful"
    INFORMATIVE = "informative"
    HUMOROUS = "humorous"
    NEUTRAL = "neutral"


class UrgencyLevel(str, Enum):
    """How time-sensitive the ad feels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class AdInputType(str, Enum):
    """Discriminator for which kind of ad input was provided."""

    IMAGE_UPLOAD = "image_upload"
    IMAGE_URL = "image_url"
    AD_PAGE_URL = "ad_page_url"


# ── Input ──────────────────────────────────────────────────────────────────────


class AdInput(BaseModel):
    """
    Ad creative input — exactly ONE of the three fields must be populated.

    Validated at model level via `@model_validator`.
    """

    ad_image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded ad image (PNG/JPEG). Provided on file upload.",
    )
    ad_image_url: Optional[HttpUrl] = Field(
        default=None,
        description="Public URL pointing to the ad image.",
    )
    ad_page_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL of a page containing the ad (e.g., social media post).",
    )

    @model_validator(mode="after")
    def _exactly_one_input(self) -> "AdInput":
        """Ensure exactly one input field is populated."""
        provided = sum(
            v is not None
            for v in (self.ad_image_base64, self.ad_image_url, self.ad_page_url)
        )
        if provided == 0:
            raise ValueError(
                "Exactly one of ad_image_base64, ad_image_url, or ad_page_url "
                "must be provided."
            )
        if provided > 1:
            raise ValueError(
                "Only one of ad_image_base64, ad_image_url, or ad_page_url "
                "may be provided."
            )
        return self

    @property
    def input_type(self) -> AdInputType:
        """Discriminator for which input path to use."""
        if self.ad_image_base64 is not None:
            return AdInputType.IMAGE_UPLOAD
        if self.ad_image_url is not None:
            return AdInputType.IMAGE_URL
        return AdInputType.AD_PAGE_URL


# ── Output ─────────────────────────────────────────────────────────────────────


class AdAnalysis(BaseModel):
    """
    Structured extraction of ad creative messaging signals.

    Consumed by the edit-generation chain to personalize landing pages.
    Designed for deterministic structured output via `with_structured_output`.
    """

    # ── Core messaging ──────────────────────────────────────────────────

    headline: str = Field(
        ...,
        description="Primary headline or hook of the ad.",
    )
    offer: Optional[str] = Field(
        default=None,
        description="Specific offer or deal (e.g., '50% off', 'free trial').",
    )
    value_proposition: str = Field(
        ...,
        description="Core benefit or value the ad promises to the viewer.",
    )
    product_or_service: Optional[str] = Field(
        default=None,
        description="The product or service being advertised.",
    )

    # ── Audience & intent ───────────────────────────────────────────────

    target_audience: str = Field(
        ...,
        description=(
            "Inferred target audience "
            "(e.g., 'first-time buyers', 'fitness enthusiasts')."
        ),
    )
    audience_pain_points: list[str] = Field(
        default_factory=list,
        description="Key pain points or desires the ad addresses.",
    )

    # ── Tone & style ────────────────────────────────────────────────────

    tone: AdTone = Field(
        ...,
        description="Primary perceived tone of the ad.",
    )
    secondary_tones: list[AdTone] = Field(
        default_factory=list,
        description="Additional tones detected in multifaceted creatives.",
    )
    brand_voice_notes: Optional[str] = Field(
        default=None,
        description="Free-text notes on brand voice or personality cues.",
    )

    # ── CTA ─────────────────────────────────────────────────────────────

    cta_text: Optional[str] = Field(
        default=None,
        description="Call-to-action text (e.g., 'Shop Now', 'Get Started').",
    )
    cta_urgency: UrgencyLevel = Field(
        default=UrgencyLevel.NONE,
        description="How urgently the CTA pushes action.",
    )

    # ── Supplementary ───────────────────────────────────────────────────

    key_phrases: list[str] = Field(
        default_factory=list,
        description="Important phrases or keywords extracted from the ad.",
    )
    visual_description: Optional[str] = Field(
        default=None,
        description=(
            "Brief description of key visual elements "
            "(colors, imagery, layout)."
        ),
    )
    trust_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Trust cues found in the ad "
            "(e.g., '10k+ reviews', 'money-back guarantee')."
        ),
    )

    # ── Metadata ────────────────────────────────────────────────────────

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Self-assessed confidence of the analysis (0.0–1.0).",
    )
    raw_text_extracted: Optional[str] = Field(
        default=None,
        description="All text found in/on the ad creative (OCR or scrape).",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any caveats or issues encountered during analysis.",
    )
