"""
Page Agent Service — public interface for the Page Agent pipeline step.

The orchestrator imports ONLY this module.
It owns input validation, page scraping, and delegation to the chain.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.page_agent.page_analysis_chain import PageAnalysisChain
from app.page_agent.schemas import PageAgentResult, PageInput
from app.page_agent.scraper import scrape_landing_page

logger = logging.getLogger(__name__)


class PageAgentService:
    """
    Scrapes and analyses a landing page, returning a structured
    ``PageAgentResult``.

    This is the single entry point for the Page Agent pipeline step.

    Usage::

        service = PageAgentService()
        result = await service.analyze(PageInput(landing_page_url="https://..."))

    Args:
        model: LLM model override (passed through to ``PageAnalysisChain``).
        temperature: LLM temperature override (passed through to ``PageAnalysisChain``).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self._chain = PageAnalysisChain(model=model, temperature=temperature)

    # ── Public entry point ─────────────────────────────────────────────────────

    async def analyze(self, page_input: PageInput) -> PageAgentResult:
        """
        Scrape and analyse a landing page.

        Args:
            page_input: Validated ``PageInput`` with the landing page URL.

        Returns:
            ``PageAgentResult`` containing both the page structure
            (scrape result) and the LLM quality analysis.

        Raises:
            ValueError: If scraping or analysis fails validation.
            httpx.HTTPStatusError: If the page returns a non-2xx status.
        """
        url = str(page_input.landing_page_url)
        logger.info("Page Agent: scraping and analysing %s", url)

        # ── Step 1: Scrape and parse ──
        page_structure = await scrape_landing_page(url)
        logger.info(
            "Page Agent: scraped %d sections from %s",
            len(page_structure.sections),
            url,
        )

        # ── Step 2: Run LLM analysis chain ──
        page_analysis = await self._chain.run(page_structure.sections)
        logger.info(
            "Page Agent: analysis complete — overall_score=%.2f, confidence=%.2f",
            page_analysis.overall_page_score,
            page_analysis.confidence,
        )

        # ── Step 3: Return combined result ──
        return PageAgentResult(
            page_structure=page_structure,
            page_analysis=page_analysis,
        )
