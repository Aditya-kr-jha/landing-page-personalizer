"""
Renderer Service — public interface for the Renderer pipeline step (Step 4).

The orchestrator imports ONLY this module.
It owns input validation, guardrail execution, rendering delegation,
and confidence score computation.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config import settings
from app.renderer.guardrails import run_guardrails
from app.renderer.html_renderer import render_edits
from app.renderer.schemas import RenderInput, RenderResult

logger = logging.getLogger(__name__)


class RendererService:
    """
    Validates and applies an edit plan to a landing page's HTML.

    This is the single entry point for the Renderer pipeline step.

    Pipeline flow inside ``render()``:
      1. Run guardrails on the edit plan.
      2. Filter out blocked edits.
      3. Apply remaining edits to the DOM.
      4. Compute confidence score.
      5. Assemble and return ``RenderResult``.

    Usage::

        service = RendererService()
        result = await service.render(RenderInput(
            edit_plan=...,
            page_structure=...,
            ad_analysis=...,
            page_analysis=...,
        ))
    """

    # ── Public entry point ─────────────────────────────────────────────────────

    async def render(self, render_input: RenderInput) -> RenderResult:
        """
        Validate and apply edits to produce a personalized HTML page.

        Args:
            render_input: Validated ``RenderInput`` bundling EditPlan,
                PageStructure, AdAnalysis, and PageAnalysis from
                Steps 1–3.

        Returns:
            ``RenderResult`` with personalized HTML, edit audit trail,
            guardrail report, and confidence score.
        """
        raw_html = render_input.page_structure.raw_html
        edit_plan = render_input.edit_plan

        logger.info(
            "Renderer: starting — %d edits proposed for %s",
            len(edit_plan.edits),
            render_input.page_structure.url,
        )

        # ── Step 1: Run guardrails ──────────────────────────────────────

        guardrail_result = run_guardrails(
            edit_plan=edit_plan,
            page_structure=render_input.page_structure,
            ad_analysis=render_input.ad_analysis,
        )

        logger.info(
            "Renderer: guardrails complete — %d warnings, %d blocked",
            len(guardrail_result.all_warnings),
            len(guardrail_result.blocked_section_ids),
        )

        # ── Step 2: Filter blocked edits ────────────────────────────────

        blocked_ids = set(guardrail_result.blocked_section_ids)
        clean_edits = [
            e for e in edit_plan.edits
            if e.section_id not in blocked_ids
        ]

        logger.info(
            "Renderer: %d edits passed guardrails (of %d total)",
            len(clean_edits),
            len(edit_plan.edits),
        )

        # ── Step 3: Apply edits to DOM ──────────────────────────────────

        if clean_edits:
            personalized_html, applied, skipped = render_edits(
                raw_html=raw_html,
                edits=clean_edits,
                sections=render_input.page_structure.sections,
                enable_fuzzy=settings.RENDERER_ENABLE_FUZZY_MATCHING,
            )
        else:
            # No edits to apply — return original HTML.
            personalized_html = raw_html
            applied = []
            skipped = []

        # Add guardrail-blocked edits to the skipped list.
        from app.renderer.schemas import SkippedEdit
        for edit in edit_plan.edits:
            if edit.section_id in blocked_ids:
                skipped.append(
                    SkippedEdit(
                        section_id=edit.section_id,
                        edit_type=edit.edit_type,
                        reason=(
                            f"Blocked by guardrail: "
                            f"{_find_block_reason(guardrail_result, edit.section_id)}"
                        ),
                    )
                )

        # ── Step 4: Compute confidence ──────────────────────────────────

        confidence = self._compute_confidence(
            base_confidence=edit_plan.confidence,
            total_edits=len(edit_plan.edits),
            applied_count=len(applied),
            warning_count=len(guardrail_result.all_warnings),
        )

        # ── Step 5: Assemble summary warnings ──────────────────────────

        summary_warnings = [w.message for w in guardrail_result.all_warnings]
        if skipped:
            summary_warnings.append(
                f"{len(skipped)} edit(s) could not be applied."
            )

        logger.info(
            "Renderer: complete — %d applied, %d skipped, "
            "confidence=%.2f",
            len(applied),
            len(skipped),
            confidence,
        )

        return RenderResult(
            personalized_html=personalized_html,
            original_html=raw_html,
            edits_applied=applied,
            edits_skipped=skipped,
            guardrail_result=guardrail_result,
            confidence_score=confidence,
            warnings=summary_warnings,
        )

    # ── Confidence score computation ───────────────────────────────────────────

    @staticmethod
    def _compute_confidence(
        base_confidence: float,
        total_edits: int,
        applied_count: int,
        warning_count: int,
    ) -> float:
        """
        Compute the final confidence score for the personalization.

        Formula:
          base × edit_success_ratio − (0.05 × warnings)

        Clamped to [0.0, 1.0].
        """
        if total_edits == 0:
            # No edits proposed — nothing to personalise.
            return 0.0

        edit_success_ratio = applied_count / total_edits
        guardrail_penalty = 0.05 * warning_count

        final = base_confidence * edit_success_ratio - guardrail_penalty
        return max(0.0, min(1.0, final))


# ── Helpers ────────────────────────────────────────────────────────────────────


def _find_block_reason(
    guardrail_result,
    section_id: str,
) -> str:
    """Find the guardrail check name that blocked a section."""
    for check in guardrail_result.checks:
        if section_id in check.blocked_section_ids:
            return check.check_name.value
    return "unknown guardrail"
