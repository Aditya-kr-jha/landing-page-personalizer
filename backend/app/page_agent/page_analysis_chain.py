"""
Page Analysis Chain — LangChain wiring for the Page Agent.

Uses ``with_structured_output(PageAnalysis, method="json_schema")`` for
deterministic, schema-validated responses from GPT-4o.

Single path: text-only analysis of serialised page sections.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from app.config import settings
from app.page_agent.prompts.page_analysis import PAGE_ANALYSIS_PROMPT
from app.page_agent.schemas import NON_EDITABLE_SECTION_TYPES, PageAnalysis, PageSection

logger = logging.getLogger(__name__)

# Maximum characters of text_content to send per section.
# Keeps the prompt within reasonable input-token bounds.
_MAX_SECTION_TEXT_LEN = 500


class PageAnalysisChain:
    """
    LangChain chain that analyses landing-page sections and returns
    a typed ``PageAnalysis``.

    Uses ``with_structured_output(schema, method="json_schema")`` for
    deterministic, schema-validated responses — no manual output parsing.

    Args:
        model: LLM model name override (defaults to ``settings.PAGE_AGENT_MODEL``).
        temperature: LLM temperature override
            (defaults to ``settings.PAGE_AGENT_TEMPERATURE``).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.model = model or settings.PAGE_AGENT_MODEL
        self.temperature = (
            temperature
            if temperature is not None
            else settings.PAGE_AGENT_TEMPERATURE
        )

        self._llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=settings.OPENAI_API_KEY,
            max_tokens=16384,
        )

        # Structured output — deterministic JSON conforming to PageAnalysis
        self._structured_llm = self._llm.with_structured_output(
            PageAnalysis,
            method="json_schema",
        )

        # Pre-built chain
        self._chain = PAGE_ANALYSIS_PROMPT | self._structured_llm

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run(self, sections: list[PageSection]) -> PageAnalysis:
        """
        Analyse landing-page sections and return a typed ``PageAnalysis``.

        Args:
            sections: List of parsed ``PageSection`` objects from the scraper.

        Returns:
            Structured ``PageAnalysis`` with quality scores and recommendations.

        Raises:
            ValueError: If no sections are provided.
        """
        if not sections:
            raise ValueError("Cannot analyse an empty list of sections.")

        # Filter out non-editable sections (nav, footer) — these are
        # structural and never rewritten by Step 3, so don't waste tokens.
        editable = [
            s for s in sections
            if s.section_type not in NON_EDITABLE_SECTION_TYPES
        ]
        if not editable:
            raise ValueError(
                "No editable sections found — page may be a nav-only or "
                "footer-only fragment."
            )

        skipped = len(sections) - len(editable)
        if skipped:
            logger.info(
                "Filtered %d non-editable sections (nav/footer) — "
                "sending %d editable sections to LLM",
                skipped,
                len(editable),
            )

        # Build lean LLM-facing view: only section_id, type, and
        # truncated text.  html_content and css_selector stay in
        # PageStructure for the Step 4 renderer — the LLM never sees them.
        sections_data = [
            {
                "section_id": s.section_id,
                "section_type": s.section_type.value,
                "text_content": (
                    s.text_content[:_MAX_SECTION_TEXT_LEN] + "…"
                    if len(s.text_content) > _MAX_SECTION_TEXT_LEN
                    else s.text_content
                ),
            }
            for s in editable
        ]
        sections_json = json.dumps(sections_data, indent=2)

        logger.info(
            "Running page analysis chain "
            "(model=%s, temp=%.2f, sections=%d, json_len=%d)",
            self.model,
            self.temperature,
            len(sections),
            len(sections_json),
        )

        result: PageAnalysis = await self._chain.ainvoke(
            {"sections_json": sections_json}
        )

        logger.debug(
            "Page analysis complete: overall_score=%.2f, confidence=%.2f, "
            "section_scores=%d",
            result.overall_page_score,
            result.confidence,
            len(result.section_scores),
        )
        return result
