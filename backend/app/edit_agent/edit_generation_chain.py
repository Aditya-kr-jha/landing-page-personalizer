"""
Edit Generation Chain — LangChain wiring for the Edit Agent.

Uses ``with_structured_output(EditPlan, method="json_schema")`` for
deterministic, schema-validated responses.

Builds a **lean composite prompt** from AdAnalysis + PageStructure +
PageAnalysis, sending only the fields the LLM needs and nothing more.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from app.ad_agent.schemas import AdAnalysis
from app.config import settings
from app.edit_agent.prompts.edit_generation import EDIT_GENERATION_PROMPT
from app.edit_agent.schemas import EditPlan
from app.page_agent.schemas import (
    NON_EDITABLE_SECTION_TYPES,
    PageAnalysis,
    PageStructure,
)

logger = logging.getLogger(__name__)

# Maximum characters of text_content to include per section in the LLM prompt.
_MAX_SECTION_TEXT_LEN = 500


class EditGenerationChain:
    """
    LangChain chain that generates a structured ``EditPlan`` from
    ad analysis + page data.

    Uses ``with_structured_output(schema, method="json_schema")`` for
    deterministic, schema-validated responses — no manual output parsing.

    Args:
        model: LLM model name override
            (defaults to ``settings.EDIT_AGENT_MODEL``).
        temperature: LLM temperature override
            (defaults to ``settings.EDIT_AGENT_TEMPERATURE``).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.model = model or settings.EDIT_AGENT_MODEL
        self.temperature = (
            temperature if temperature is not None else settings.EDIT_AGENT_TEMPERATURE
        )

        self._llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=settings.OPENAI_API_KEY,
            max_tokens=16384,
        )

        # Structured output — deterministic JSON conforming to EditPlan
        self._structured_llm = self._llm.with_structured_output(
            EditPlan,
            method="json_schema",
        )

        # Pre-built chain
        self._chain = EDIT_GENERATION_PROMPT | self._structured_llm

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run(
        self,
        *,
        ad_analysis: AdAnalysis,
        page_structure: PageStructure,
        page_analysis: PageAnalysis,
    ) -> EditPlan:
        """
        Generate an edit plan that aligns the page with the ad.

        Builds lean prompt payloads from the three inputs — no raw HTML,
        no CSS selectors, no full quality scores.

        Args:
            ad_analysis: Structured ad signals from Step 1.
            page_structure: Scraped page sections from Step 2.
            page_analysis: Quality assessment from Step 2.

        Returns:
            Structured ``EditPlan`` with per-section edits.
        """
        ad_summary_json = self._build_ad_summary(ad_analysis)
        page_sections_json = self._build_page_sections(page_structure)
        page_weaknesses_json = self._build_page_weaknesses(page_analysis)

        logger.info(
            "Running edit generation chain "
            "(model=%s, temp=%.2f, ad_json=%d, sections_json=%d, "
            "weaknesses_json=%d chars)",
            self.model,
            self.temperature,
            len(ad_summary_json),
            len(page_sections_json),
            len(page_weaknesses_json),
        )

        result: EditPlan = await self._chain.ainvoke(
            {
                "ad_summary_json": ad_summary_json,
                "page_sections_json": page_sections_json,
                "page_weaknesses_json": page_weaknesses_json,
            }
        )

        logger.debug(
            "Edit generation complete: %d edits, confidence=%.2f, " "warnings=%d",
            len(result.edits),
            result.confidence,
            len(result.warnings),
        )
        return result

    # ── Lean prompt builders ───────────────────────────────────────────────────

    @staticmethod
    def _build_ad_summary(ad: AdAnalysis) -> str:
        """
        Build lean JSON from AdAnalysis — only the fields the LLM needs
        to decide what to edit.
        """
        data = {
            "headline": ad.headline,
            "offer": ad.offer,
            "value_proposition": ad.value_proposition,
            "product_or_service": ad.product_or_service,
            "target_audience": ad.target_audience,
            "audience_pain_points": ad.audience_pain_points,
            "tone": ad.tone.value,
            "cta_text": ad.cta_text,
            "cta_urgency": ad.cta_urgency.value,
            "key_phrases": ad.key_phrases,
            "trust_signals": ad.trust_signals,
        }
        # Strip None values to keep the prompt compact.
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, indent=2)

    @staticmethod
    def _build_page_sections(page: PageStructure) -> str:
        """
        Build lean JSON of page sections — only section_id, type, and
        truncated text_content.  Filters out non-editable sections.
        """
        sections_data = []
        for s in page.sections:
            if s.section_type in NON_EDITABLE_SECTION_TYPES:
                continue
            text = s.text_content
            if len(text) > _MAX_SECTION_TEXT_LEN:
                text = text[:_MAX_SECTION_TEXT_LEN] + "…"
            sections_data.append(
                {
                    "section_id": s.section_id,
                    "section_type": s.section_type.value,
                    "text_content": text,
                }
            )
        return json.dumps(sections_data, indent=2)

    @staticmethod
    def _build_page_weaknesses(analysis: PageAnalysis) -> str:
        """
        Build lean JSON from PageAnalysis — only the top-level signals
        the LLM needs to prioritise which sections to edit.
        """
        data = {
            "overall_page_score": analysis.overall_page_score,
            "key_weaknesses": analysis.key_weaknesses,
            "recommendations": analysis.recommendations,
        }
        return json.dumps(data, indent=2)
