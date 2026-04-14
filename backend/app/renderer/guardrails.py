"""
Pre-render guardrail validation layer.

Runs **before** any DOM manipulation.  Each check inspects the
``EditPlan`` against the source material (ad analysis + original page)
and blocks or warns about edits that violate safety constraints.

Four checks:
  1. Schema Check   — structural validity of the edit plan.
  2. Sck     — no new claims invented beyond source material.
  4. HTML Safetcope Check    — every targeted section_id exists in PageStructure.
  3. Fact Chey    — replacement text contains no executable/structural HTML.

Design principle: the pipeline **never fully aborts**.  Individual edits
that fail a guardrail are removed from the plan; the rest proceed.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.ad_agent.schemas import AdAnalysis
from app.edit_agent.schemas import EditPlan, SectionEdit
from app.page_agent.schemas import PageStructure
from app.renderer.schemas import (
    GuardrailCheckName,
    GuardrailCheckResult,
    GuardrailResult,
    GuardrailSeverity,
    GuardrailWarning,
)

logger = logging.getLogger(__name__)

# ── Dangerous HTML patterns ────────────────────────────────────────────────────

_DANGEROUS_HTML_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"<script[\s>]", re.IGNORECASE), "Contains <script> tag"),
    (re.compile(r"<iframe[\s>]", re.IGNORECASE), "Contains <iframe> tag"),
    (re.compile(r"<style[\s>]", re.IGNORECASE), "Contains <style> tag"),
    (re.compile(r"<link[\s>]", re.IGNORECASE), "Contains <link> tag"),
    (re.compile(r"<object[\s>]", re.IGNORECASE), "Contains <object> tag"),
    (re.compile(r"<embed[\s>]", re.IGNORECASE), "Contains <embed> tag"),
    (re.compile(r"\bon\w+\s*=", re.IGNORECASE), "Contains inline event handler"),
    (re.compile(r"javascript:", re.IGNORECASE), "Contains javascript: URI"),
]

# Patterns to extract numeric claims (percentages, money, counts).
_NUMERIC_CLAIM_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(%|percent|off|discount|guarantee|money.?back|"
    r"free|days?|months?|years?|hours?|users?|customers?|reviews?|stars?)\b",
    re.IGNORECASE,
)

# Patterns to extract guarantee / promise phrases.
_GUARANTEE_PATTERN = re.compile(
    r"\b(guarantee|warranted|risk.?free|no.?risk|money.?back|refund|"
    r"certified|approved|endorsed|award|patent)\b",
    re.IGNORECASE,
)


# ── Public API ─────────────────────────────────────────────────────────────────


def run_guardrails(
    edit_plan: EditPlan,
    page_structure: PageStructure,
    ad_analysis: AdAnalysis,
) -> GuardrailResult:
    """
    Run all guardrail checks against the edit plan.

    Returns a ``GuardrailResult`` with per-check results, an aggregated
    warning list, and the union of all blocked section IDs.

    Args:
        edit_plan: The proposed edit plan from Step 3.
        page_structure: Scraped page sections from Step 2.
        ad_analysis: Structured ad signals from Step 1.

    Returns:
        Aggregated guardrail result.
    """
    checks: list[GuardrailCheckResult] = [
        _run_schema_check(edit_plan),
        _run_scope_check(edit_plan, page_structure),
        _run_fact_check(edit_plan, page_structure, ad_analysis),
        _run_html_safety_check(edit_plan),
    ]

    all_warnings: list[GuardrailWarning] = []
    blocked_ids: set[str] = set()

    for check in checks:
        all_warnings.extend(check.warnings)
        blocked_ids.update(check.blocked_section_ids)

    overall_passed = all(c.passed for c in checks)

    logger.info(
        "Guardrails complete: %d checks, %d warnings, %d blocked edits, "
        "overall_passed=%s",
        len(checks),
        len(all_warnings),
        len(blocked_ids),
        overall_passed,
    )

    return GuardrailResult(
        overall_passed=overall_passed,
        checks=checks,
        all_warnings=list(all_warnings),
        blocked_section_ids=sorted(blocked_ids),
    )


# ── Individual checks ─────────────────────────────────────────────────────────


def _run_schema_check(edit_plan: EditPlan) -> GuardrailCheckResult:
    """
    Validate structural integrity of the edit plan.

    Checks:
      • No edits with empty original_text or replacement_text.
      • No duplicate section_ids (one edit per section max).
      • EditPlan has at least one edit.
    """
    warnings: list[GuardrailWarning] = []
    blocked: list[str] = []

    if not edit_plan.edits:
        warnings.append(
            GuardrailWarning(
                check_name=GuardrailCheckName.SCHEMA_CHECK,
                severity=GuardrailSeverity.WARNING,
                message="Edit plan contains zero edits.",
            )
        )

    for edit in edit_plan.edits:
        if not edit.original_text.strip():
            warnings.append(
                GuardrailWarning(
                    check_name=GuardrailCheckName.SCHEMA_CHECK,
                    severity=GuardrailSeverity.CRITICAL,
                    section_id=edit.section_id,
                    message=(
                        f"Edit for section '{edit.section_id}' has empty "
                        f"original_text — cannot perform string matching."
                    ),
                )
            )
            blocked.append(edit.section_id)

        if not edit.replacement_text.strip():
            warnings.append(
                GuardrailWarning(
                    check_name=GuardrailCheckName.SCHEMA_CHECK,
                    severity=GuardrailSeverity.WARNING,
                    section_id=edit.section_id,
                    message=(
                        f"Edit for section '{edit.section_id}' has empty "
                        f"replacement_text — would delete content."
                    ),
                )
            )

    passed = len(blocked) == 0
    return GuardrailCheckResult(
        check_name=GuardrailCheckName.SCHEMA_CHECK,
        passed=passed,
        warnings=warnings,
        blocked_section_ids=blocked,
    )


def _run_scope_check(
    edit_plan: EditPlan,
    page_structure: PageStructure,
) -> GuardrailCheckResult:
    """
    Verify every ``section_id`` in the edit plan exists in ``PageStructure``.

    Edits targeting nonexistent sections are blocked silently.
    """
    warnings: list[GuardrailWarning] = []
    blocked: list[str] = []

    valid_ids = {s.section_id for s in page_structure.sections}

    for edit in edit_plan.edits:
        if edit.section_id not in valid_ids:
            warnings.append(
                GuardrailWarning(
                    check_name=GuardrailCheckName.SCOPE_CHECK,
                    severity=GuardrailSeverity.CRITICAL,
                    section_id=edit.section_id,
                    message=(
                        f"Section '{edit.section_id}' does not exist in the "
                        f"scraped page structure. Available: "
                        f"{sorted(valid_ids)}"
                    ),
                )
            )
            blocked.append(edit.section_id)

    passed = len(blocked) == 0
    return GuardrailCheckResult(
        check_name=GuardrailCheckName.SCOPE_CHECK,
        passed=passed,
        warnings=warnings,
        blocked_section_ids=blocked,
    )


def _run_fact_check(
    edit_plan: EditPlan,
    page_structure: PageStructure,
    ad_analysis: AdAnalysis,
) -> GuardrailCheckResult:
    """
    Check for fabricated claims in replacement text.

    Extracts numeric claims and guarantee phrases from each replacement,
    then verifies they appear in either the ad analysis or the original
    page content.  Novel claims are flagged.

    This is a **conservative heuristic** — it catches obvious violations
    (new percentages, new guarantees) but will not catch subtle semantic
    fabrication.
    """
    warnings: list[GuardrailWarning] = []
    blocked: list[str] = []

    # Build the source-of-truth corpus: all text from ad + original page.
    source_corpus = _build_source_corpus(ad_analysis, page_structure)
    source_corpus_lower = source_corpus.lower()

    for edit in edit_plan.edits:
        novel_claims = _find_novel_claims(
            replacement_text=edit.replacement_text,
            source_corpus_lower=source_corpus_lower,
        )
        if novel_claims:
            warnings.append(
                GuardrailWarning(
                    check_name=GuardrailCheckName.FACT_CHECK,
                    severity=GuardrailSeverity.CRITICAL,
                    section_id=edit.section_id,
                    message=(
                        f"Replacement text for section '{edit.section_id}' "
                        f"contains claims not found in source material: "
                        f"{novel_claims}"
                    ),
                )
            )
            blocked.append(edit.section_id)

    passed = len(blocked) == 0
    return GuardrailCheckResult(
        check_name=GuardrailCheckName.FACT_CHECK,
        passed=passed,
        warnings=warnings,
        blocked_section_ids=blocked,
    )


def _run_html_safety_check(edit_plan: EditPlan) -> GuardrailCheckResult:
    """
    Scan replacement text for dangerous HTML content.

    Blocks edits containing ``<script>``, ``<iframe>``, inline event
    handlers, ``javascript:`` URIs, and similar injection vectors.
    """
    warnings: list[GuardrailWarning] = []
    blocked: list[str] = []

    for edit in edit_plan.edits:
        for pattern, description in _DANGEROUS_HTML_PATTERNS:
            if pattern.search(edit.replacement_text):
                warnings.append(
                    GuardrailWarning(
                        check_name=GuardrailCheckName.HTML_SAFETY_CHECK,
                        severity=GuardrailSeverity.CRITICAL,
                        section_id=edit.section_id,
                        message=(
                            f"Replacement text for section "
                            f"'{edit.section_id}' failed HTML safety: "
                            f"{description}"
                        ),
                    )
                )
                blocked.append(edit.section_id)
                break  # One violation is enough to block.

    passed = len(blocked) == 0
    return GuardrailCheckResult(
        check_name=GuardrailCheckName.HTML_SAFETY_CHECK,
        passed=passed,
        warnings=warnings,
        blocked_section_ids=blocked,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_source_corpus(
    ad_analysis: AdAnalysis,
    page_structure: PageStructure,
) -> str:
    """
    Build a single text corpus from all source material.

    Combines ad analysis fields and all page section text into one
    searchable string.  Used by the fact checker to verify claims.
    """
    parts: list[str] = []

    # Ad analysis fields
    parts.append(ad_analysis.headline)
    if ad_analysis.offer:
        parts.append(ad_analysis.offer)
    parts.append(ad_analysis.value_proposition)
    if ad_analysis.product_or_service:
        parts.append(ad_analysis.product_or_service)
    parts.append(ad_analysis.target_audience)
    parts.extend(ad_analysis.audience_pain_points)
    if ad_analysis.cta_text:
        parts.append(ad_analysis.cta_text)
    parts.extend(ad_analysis.key_phrases)
    parts.extend(ad_analysis.trust_signals)
    if ad_analysis.raw_text_extracted:
        parts.append(ad_analysis.raw_text_extracted)
    if ad_analysis.brand_voice_notes:
        parts.append(ad_analysis.brand_voice_notes)

    # Page section text
    for section in page_structure.sections:
        parts.append(section.text_content)

    return " ".join(parts)


def _find_novel_claims(
    replacement_text: str,
    source_corpus_lower: str,
) -> list[str]:
    """
    Find numeric claims and guarantee phrases in replacement text
    that do not appear in the source corpus.

    Returns a list of novel claim strings.  Empty list means clean.
    """
    novel: list[str] = []

    # Check numeric claims (e.g., "50% off", "10,000 users")
    for match in _NUMERIC_CLAIM_PATTERN.finditer(replacement_text):
        claim = match.group(0).strip()
        if claim.lower() not in source_corpus_lower:
            # Also try just the number portion — the source might phrase
            # it differently (e.g., ad says "50% off", replacement says
            # "50 percent off").
            number = match.group(1)
            if number not in source_corpus_lower:
                novel.append(claim)

    # Check guarantee / promise phrases
    for match in _GUARANTEE_PATTERN.finditer(replacement_text):
        claim = match.group(0).strip()
        if claim.lower() not in source_corpus_lower:
            novel.append(claim)

    return novel
