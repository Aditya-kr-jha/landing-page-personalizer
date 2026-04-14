"""
Edit Agent Service — public interface for the Edit Agent pipeline step.

The orchestrator imports ONLY this module.
It owns input validation and delegation to the chain.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.edit_agent.edit_generation_chain import EditGenerationChain
from app.edit_agent.schemas import EditInput, EditPlan

logger = logging.getLogger(__name__)


class EditAgentService:
    """
    Generates a structured edit plan that aligns a landing page with
    an ad's messaging.

    This is the single entry point for the Edit Agent pipeline step.

    Usage::

        service = EditAgentService()
        plan = await service.generate(EditInput(
            ad_analysis=...,
            page_structure=...,
            page_analysis=...,
        ))

    Args:
        model: LLM model override (passed through to ``EditGenerationChain``).
        temperature: LLM temperature override
            (passed through to ``EditGenerationChain``).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self._chain = EditGenerationChain(model=model, temperature=temperature)

    # ── Public entry point ─────────────────────────────────────────────────────

    async def generate(self, edit_input: EditInput) -> EditPlan:
        """
        Generate an edit plan from ad analysis + page data.

        Args:
            edit_input: Validated ``EditInput`` bundling AdAnalysis,
                PageStructure, and PageAnalysis from Steps 1–2.

        Returns:
            Structured ``EditPlan`` with per-section text replacements,
            strategy explanation, and confidence scores.

        Raises:
            ValueError: If input validation fails.
        """
        logger.info(
            "Edit Agent: generating edit plan for %s (%d sections)",
            edit_input.page_structure.url,
            len(edit_input.page_structure.sections),
        )

        edit_plan = await self._chain.run(
            ad_analysis=edit_input.ad_analysis,
            page_structure=edit_input.page_structure,
            page_analysis=edit_input.page_analysis,
        )

        logger.info(
            "Edit Agent: plan generated — %d edits, confidence=%.2f",
            len(edit_plan.edits),
            edit_plan.confidence,
        )

        return edit_plan
