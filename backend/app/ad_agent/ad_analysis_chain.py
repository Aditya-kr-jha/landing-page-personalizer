"""
Ad Analysis Chain — LangChain wiring for the Ad Agent.

Uses `with_structured_output(AdAnalysis, method="json_schema")` for
deterministic, schema-validated responses from GPT-4o.

Two paths:
  • Image path — multimodal GPT-4o vision (upload or URL)
  • Text path  — text-only GPT-4o (scraped ad page)
"""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Optional

import httpx
from langchain_openai import ChatOpenAI
from PIL import Image

from app.ad_agent.prompts.ad_analysis import IMAGE_ANALYSIS_PROMPT, TEXT_ANALYSIS_PROMPT
from app.ad_agent.schemas import AdAnalysis, AdInputType
from app.config import settings

logger = logging.getLogger(__name__)

# Maximum image dimension (width or height) before resizing for the vision API.
_MAX_IMAGE_DIM = 1024


class AdAnalysisChain:
    """
    LangChain chain that analyses an ad creative and returns typed `AdAnalysis`.

    Uses `with_structured_output(schema, method="json_schema")` for
    deterministic, schema-validated responses — no manual output parsing.

    Args:
        model: LLM model name override (defaults to ``settings.AD_AGENT_MODEL``).
        temperature: LLM temperature override
            (defaults to ``settings.AD_AGENT_TEMPERATURE``).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.model = model or settings.AD_AGENT_MODEL
        self.temperature = (
            temperature
            if temperature is not None
            else settings.AD_AGENT_TEMPERATURE
        )

        self._llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=settings.OPENAI_API_KEY,
            max_tokens=2048,
        )

        # Structured output — deterministic JSON conforming to AdAnalysis
        self._structured_llm = self._llm.with_structured_output(
            AdAnalysis,
            method="json_schema",
        )

        # Pre-built chains
        self._image_chain = IMAGE_ANALYSIS_PROMPT | self._structured_llm
        self._text_chain = TEXT_ANALYSIS_PROMPT | self._structured_llm

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run(
        self,
        *,
        input_type: AdInputType,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        ad_page_text: Optional[str] = None,
    ) -> AdAnalysis:
        """
        Run the appropriate analysis chain and return a typed ``AdAnalysis``.

        Args:
            input_type: Discriminator for which input path to use.
            image_base64: Base64-encoded image data (for IMAGE_UPLOAD).
            image_url: Public image URL (for IMAGE_URL).
            ad_page_text: Scraped ad page text (for AD_PAGE_URL).

        Returns:
            Structured ``AdAnalysis`` with extracted messaging signals.

        Raises:
            ValueError: If required data for the given ``input_type`` is missing.
        """
        if input_type in (AdInputType.IMAGE_UPLOAD, AdInputType.IMAGE_URL):
            return await self._run_image_analysis(
                image_base64=image_base64,
                image_url=image_url,
                input_type=input_type,
            )

        if input_type == AdInputType.AD_PAGE_URL:
            if not ad_page_text:
                raise ValueError(
                    "ad_page_text is required for AD_PAGE_URL input type."
                )
            return await self._run_text_analysis(ad_text=ad_page_text)

        raise ValueError(f"Unknown input type: {input_type}")

    # ── Image path ─────────────────────────────────────────────────────────────

    async def _run_image_analysis(
        self,
        *,
        image_base64: Optional[str],
        image_url: Optional[str],
        input_type: AdInputType,
    ) -> AdAnalysis:
        """Analyze an ad image via multimodal GPT-4o."""
        if input_type == AdInputType.IMAGE_UPLOAD:
            if not image_base64:
                raise ValueError("image_base64 is required for IMAGE_UPLOAD.")
            data_uri = self._prepare_base64_image(image_base64)
        elif input_type == AdInputType.IMAGE_URL:
            if not image_url:
                raise ValueError("image_url is required for IMAGE_URL.")
            data_uri = await self._fetch_and_encode_image(image_url)
        else:
            raise ValueError(f"Unexpected input_type for image path: {input_type}")

        logger.info(
            "Running image analysis chain (model=%s, temp=%.2f)",
            self.model,
            self.temperature,
        )
        result: AdAnalysis = await self._image_chain.ainvoke(
            {"image_url": data_uri}
        )

        logger.debug(
            "Image analysis complete: headline=%r, confidence=%.2f",
            result.headline,
            result.confidence,
        )
        return result

    # ── Text path ──────────────────────────────────────────────────────────────

    async def _run_text_analysis(self, ad_text: str) -> AdAnalysis:
        """Analyze scraped ad page text via text-only GPT-4o."""
        logger.info(
            "Running text analysis chain (model=%s, temp=%.2f, text_len=%d)",
            self.model,
            self.temperature,
            len(ad_text),
        )
        result: AdAnalysis = await self._text_chain.ainvoke({"ad_text": ad_text})

        logger.debug(
            "Text analysis complete: headline=%r, confidence=%.2f",
            result.headline,
            result.confidence,
        )
        return result

    # ── Image helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _prepare_base64_image(b64_data: str) -> str:
        """
        Validate, resize if needed, and return a ``data:`` URI for the vision API.

        Accepts raw base64 or a full ``data:`` URI prefix.
        """
        # Strip data URI prefix if present
        if b64_data.startswith("data:"):
            _, b64_data = b64_data.split(",", 1)

        img_bytes = base64.b64decode(b64_data)
        img = Image.open(BytesIO(img_bytes))

        return AdAnalysisChain._encode_image(img)

    @staticmethod
    async def _fetch_and_encode_image(url: str) -> str:
        """Download an image URL and convert to a ``data:`` URI."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()

        img = Image.open(BytesIO(resp.content))
        return AdAnalysisChain._encode_image(img)

    @staticmethod
    def _encode_image(img: Image.Image) -> str:
        """
        Resize (if needed) and encode a PIL Image to a ``data:`` URI.

        - Images exceeding ``_MAX_IMAGE_DIM`` are thumbnailed.
        - RGBA PNGs are kept as PNG; everything else is re-encoded as JPEG.
        """
        if max(img.size) > _MAX_IMAGE_DIM:
            original_size = img.size
            img.thumbnail((_MAX_IMAGE_DIM, _MAX_IMAGE_DIM), Image.LANCZOS)
            logger.info("Resized image %s → %s", original_size, img.size)

        buf = BytesIO()
        if (img.format or "").upper() == "PNG" and img.mode == "RGBA":
            img.save(buf, format="PNG", optimize=True)
            mime = "image/png"
        else:
            img.convert("RGB").save(buf, format="JPEG", quality=85)
            mime = "image/jpeg"

        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
