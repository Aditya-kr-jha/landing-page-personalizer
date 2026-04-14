"""
Centralised application settings.

Reads from ``app/.env`` and environment variables.
Uses ``pydantic-settings`` for type-safe config management.
"""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

_CONFIG_DIR = Path(__file__).parent


class Settings(BaseSettings):
    """Application-wide settings loaded from env / .env."""

    # ── OpenAI ──────────────────────────────────────────────────────────────

    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API key.",
    )

    # ── Ad Agent ────────────────────────────────────────────────────────────

    AD_AGENT_MODEL: str = Field(
        default="gpt-5.4-nano",
        description="OpenAI model for ad analysis (must support vision).",
    )
    AD_AGENT_TEMPERATURE: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="LLM temperature for ad analysis. Low for factual extraction.",
    )

    # ── Page Agent ──────────────────────────────────────────────────────────

    PAGE_AGENT_MODEL: str = Field(
        default="gpt-5.4-nano",
        description="OpenAI model for page analysis.",
    )
    PAGE_AGENT_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature for page analysis. Very low for scoring.",
    )

    # ── Edit Agent ──────────────────────────────────────────────────────────

    EDIT_AGENT_MODEL: str = Field(
        default="gpt-5.4-nano",
        description="OpenAI model for edit generation.",
    )
    EDIT_AGENT_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description=(
            "LLM temperature for edit generation. "
            "Moderate for creative rewrites."
        ),
    )

    # ── Renderer ───────────────────────────────────────────────────────────

    RENDERER_MIN_CONFIDENCE_THRESHOLD: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum per-edit confidence to apply. Edits below this "
            "threshold are skipped."
        ),
    )
    RENDERER_ENABLE_FUZZY_MATCHING: bool = Field(
        default=True,
        description=(
            "Allow whitespace-normalised fuzzy matching when exact "
            "text match fails."
        ),
    )

    # ── Future agent temps go here ──────────────────────────────────────────

    class Config:
        env_file = os.path.join(_CONFIG_DIR, ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
