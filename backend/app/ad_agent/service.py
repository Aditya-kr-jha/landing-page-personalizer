"""
Ad Agent Service — public interface for the Ad Agent pipeline step.

The orchestrator imports ONLY this module.
It owns input validation, ad-page scraping, and delegation to the chain.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.ad_agent.ad_analysis_chain import AdAnalysisChain
from app.ad_agent.schemas import AdAnalysis, AdInput, AdInputType

logger = logging.getLogger(__name__)

# Minimum scraped text length to consider meaningful.
_MIN_SCRAPED_TEXT_LEN = 20


class AdAgentService:
    """
    Analyzes an ad creative and returns a structured ``AdAnalysis``.

    This is the single entry point for the Ad Agent pipeline step.

    Usage::

        service = AdAgentService()
        result = await service.analyze(AdInput(ad_image_base64="iVBOR..."))

    Args:
        model: LLM model override (passed through to ``AdAnalysisChain``).
        temperature: LLM temperature override (passed through to ``AdAnalysisChain``).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self._chain = AdAnalysisChain(model=model, temperature=temperature)

    # ── Public entry point ─────────────────────────────────────────────────────

    async def analyze(self, ad_input: AdInput) -> AdAnalysis:
        """
        Analyze an ad creative and extract messaging signals.

        Args:
            ad_input: Validated ``AdInput`` with exactly one field populated.

        Returns:
            Structured ``AdAnalysis`` for downstream pipeline consumption.

        Raises:
            ValueError: If ad page scrape yields insufficient text.
            httpx.HTTPStatusError: If ad page or image URL returns non-2xx.
        """
        input_type = ad_input.input_type
        logger.info("Ad Agent: analyzing via %s", input_type.value)

        if input_type == AdInputType.IMAGE_UPLOAD:
            return await self._chain.run(
                input_type=input_type,
                image_base64=ad_input.ad_image_base64,
            )

        if input_type == AdInputType.IMAGE_URL:
            return await self._chain.run(
                input_type=input_type,
                image_url=str(ad_input.ad_image_url),
            )

        if input_type == AdInputType.AD_PAGE_URL:
            ad_text = await self._scrape_ad_page(str(ad_input.ad_page_url))
            return await self._chain.run(
                input_type=input_type,
                ad_page_text=ad_text,
            )

        raise ValueError(f"Unsupported input type: {input_type}")

    # ── Scraping ───────────────────────────────────────────────────────────────

    @staticmethod
    async def _scrape_ad_page(url: str) -> str:
        """
        Fetch an ad page and extract visible text content.

        Strips scripts, styles, nav, footer, header, and iframe elements
        to focus on actual ad content.

        Args:
            url: The ad page URL to scrape.

        Returns:
            Cleaned text content from the page.

        Raises:
            ValueError: If the scraped text is too short to be meaningful.
            httpx.HTTPStatusError: If the page returns a non-2xx status.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise elements
        for tag in soup(
            ["script", "style", "noscript", "nav", "footer", "header", "iframe"]
        ):
            tag.decompose()

        # Extract and clean visible text
        lines = [
            line.strip()
            for line in soup.get_text(separator="\n", strip=True).splitlines()
            if line.strip()
        ]
        text = "\n".join(lines)

        if len(text) < _MIN_SCRAPED_TEXT_LEN:
            raise ValueError(
                f"Could not extract meaningful text from ad page: {url} "
                f"(got {len(text)} chars)"
            )

        logger.debug("Scraped ad page %s — %d chars extracted", url, len(text))
        return text
