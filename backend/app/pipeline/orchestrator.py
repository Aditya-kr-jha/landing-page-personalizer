"""
Core Pipeline Orchestrator.

Logic-free data sequencing. Simply passes the strongly typed data objects
from service to service in the correct sequence. 
Executes Step 1 and 2 independently via asyncio.gather to minimize latency.
"""

from __future__ import annotations

import asyncio
import logging

from app.ad_agent.service import AdAgentService
from app.edit_agent.schemas import EditInput
from app.edit_agent.service import EditAgentService
from app.page_agent.service import PageAgentService
from app.pipeline.schemas import PipelineInput, PipelineResult
from app.renderer.schemas import RenderInput
from app.renderer.service import RendererService

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    High-level orchestrator class responsible for assembling the four independent
    pipeline services: AdAgent, PageAgent, EditAgent, and Renderer.

    The Orchestrator strictly handles data exchange and sequence parallelization
    without any intrinsic business logic or ML logic.
    """

    def __init__(
        self,
        ad_agent: AdAgentService | None = None,
        page_agent: PageAgentService | None = None,
        edit_agent: EditAgentService | None = None,
        renderer: RendererService | None = None,
    ) -> None:
        """Initialize the pipeline manually or via Dependency Injection."""
        self.ad_agent = ad_agent or AdAgentService()
        self.page_agent = page_agent or PageAgentService()
        self.edit_agent = edit_agent or EditAgentService()
        self.renderer = renderer or RendererService()

    async def run(self, pipeline_input: PipelineInput) -> PipelineResult:
        """
        Execute the end-to-end personalization pipeline automatically.

        Args:
            pipeline_input: Object containing strictly typed inputs for both ad
            analysis and page structure parsing.

        Returns:
            PipelineResult encapsulating the terminal output and audit trace.

        Raises:
            Will bubble any exceptions thrown by downstream layers natively. Let
            route error-handling catch and format.
        """
        logger.info(
            "PIPELINE: Initiating E2E pipeline for url=%s",
            pipeline_input.page_input.landing_page_url,
        )

        # ── Step 1 & 2: Ad and Page Parallel Analysis ──────────────────────────
        # Optimizes round trips by scraping and scanning image concurrently.
        logger.debug("PIPELINE: Submitting parallel Step 1 (Ad) and Step 2 (Page) requests.")
        ad_analysis, page_result = await asyncio.gather(
            self.ad_agent.analyze(pipeline_input.ad_input),
            self.page_agent.analyze(pipeline_input.page_input),
        )
        logger.info("PIPELINE: Parallel initial analysis complete.")
        logger.info(f"DEBUG ad_analysis: {str(ad_analysis)[:300]}...")
        logger.info(f"DEBUG page_analysis: {str(page_result.page_analysis)[:300]}...")
        logger.info(f"DEBUG page_structure (num sections): {len(page_result.page_structure.sections)}")

        # ── Step 3: Generative Editing ──────────────────────────────────────────
        logger.debug("PIPELINE: Proceeding to Step 3 (Generation).")
        edit_input = EditInput(
            ad_analysis=ad_analysis,
            page_structure=page_result.page_structure,
            page_analysis=page_result.page_analysis,
        )
        edit_plan = await self.edit_agent.generate(edit_input)
        logger.info(
            "PIPELINE: Generation complete — %d edits proposed (Confidence: %.2f)",
            len(edit_plan.edits),
            edit_plan.confidence,
        )
        logger.info(f"DEBUG edit_plan: {str(edit_plan.edits)[:500]}...")

        # ── Step 4: Render DOM modifications ────────────────────────────────────
        logger.debug("PIPELINE: Proceeding to Step 4 (Renderer).")
        render_input = RenderInput(
            edit_plan=edit_plan,
            page_structure=page_result.page_structure,
            ad_analysis=ad_analysis,
            page_analysis=page_result.page_analysis,
        )
        render_result = await self.renderer.render(render_input)
        logger.info(
            "PIPELINE: Rendering complete — E2E execution finished. "
            "Confidence: %.2f",
            render_result.confidence_score,
        )

        return PipelineResult(
            ad_analysis=ad_analysis,
            page_analysis=page_result.page_analysis,
            render_result=render_result,
        )
