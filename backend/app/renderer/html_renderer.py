"""
HTML Renderer — BeautifulSoup DOM manipulation engine.

Applies text replacements from the ``EditPlan`` to the raw HTML,
producing a modified page where only the copy has changed while
the structure, CSS, images, and layout remain intact.

Uses a **dual-pass** text-node replacement strategy:
  Pass 1 — Exact substring match on concatenated visible text.
  Pass 2 — Whitespace-normalised fuzzy match (collapse runs of
            whitespace, strip leading/trailing) as a fallback.

Design invariant: this module **never inserts or removes HTML tags**.
It only modifies the text content of existing ``NavigableString`` nodes.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from app.edit_agent.schemas import SectionEdit
from app.page_agent.schemas import PageSection
from app.renderer.schemas import AppliedEdit, MatchType, SkippedEdit

logger = logging.getLogger(__name__)

# Tags whose text content should never be touched during rendering.
_SKIP_TAGS: frozenset[str] = frozenset({
    "script", "style", "noscript", "template", "svg", "math",
})

# Inline formatting tags — their text children are part of the parent's
# logical text block and should be included when concatenating text nodes.
_INLINE_TAGS: frozenset[str] = frozenset({
    "em", "strong", "b", "i", "u", "span", "a", "mark", "small",
    "sub", "sup", "abbr", "cite", "code", "kbd", "s", "del", "ins",
    "q", "var", "time", "data", "dfn", "bdi", "bdo", "ruby", "rt",
    "rp", "wbr", "label",
})

# Block-ish containers that often represent one logical text block.
_BLOCK_TAGS: frozenset[str] = frozenset({
    "p", "div", "section", "article", "aside", "header", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "blockquote",
    "figcaption", "summary",
})

# Interactive containers are risky when they carry long composite text.
_INTERACTIVE_TAGS: frozenset[str] = frozenset({
    "a", "button", "label",
})


# ── Public API ─────────────────────────────────────────────────────────────────


def render_edits(
    raw_html: str,
    edits: list[SectionEdit],
    sections: list[PageSection],
    *,
    enable_fuzzy: bool = True,
) -> tuple[str, list[AppliedEdit], list[SkippedEdit]]:
    """
    Apply text replacements to the raw HTML.

    Args:
        raw_html: The full original HTML page.
        edits: List of section-level text replacements to apply.
        sections: Parsed page sections (for CSS selector lookup).
        enable_fuzzy: If ``True``, fall back to whitespace-normalised
            matching when exact match fails.

    Returns:
        A 3-tuple of:
          - Modified HTML string.
          - List of successfully applied edits.
          - List of edits that could not be applied.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    section_map = {s.section_id: s for s in sections}

    applied: list[AppliedEdit] = []
    skipped: list[SkippedEdit] = []

    for edit in edits:
        section = section_map.get(edit.section_id)
        if section is None:
            skipped.append(
                SkippedEdit(
                    section_id=edit.section_id,
                    edit_type=edit.edit_type,
                    reason=(
                        f"Section '{edit.section_id}' not found in "
                        f"section map."
                    ),
                )
            )
            continue

        # Locate the section element in the DOM.
        element = _resolve_section(soup, section)
        if element is None:
            skipped.append(
                SkippedEdit(
                    section_id=edit.section_id,
                    edit_type=edit.edit_type,
                    reason=(
                        f"CSS selector '{section.css_selector}' did not "
                        f"match any element in the DOM."
                    ),
                )
            )
            continue

        # Narrow broad section wrappers down to the safest matching node.
        target_element = _select_replacement_target(
            section_element=element,
            original_text=edit.original_text,
        )
        if target_element is None:
            skipped.append(
                SkippedEdit(
                    section_id=edit.section_id,
                    edit_type=edit.edit_type,
                    reason=(
                        f"Could not find a safe DOM target for section "
                        f"'{edit.section_id}'. The section is likely a "
                        f"composite wrapper rather than a single text block."
                    ),
                )
            )
            continue

        # Attempt text replacement.
        match_type = _apply_text_replacement(
            element=target_element,
            original_text=edit.original_text,
            replacement_text=edit.replacement_text,
            enable_fuzzy=enable_fuzzy,
        )

        if match_type is not None:
            applied.append(
                AppliedEdit(
                    section_id=edit.section_id,
                    edit_type=edit.edit_type,
                    original_text=edit.original_text,
                    replacement_text=edit.replacement_text,
                    match_type=match_type,
                    confidence=edit.confidence,
                )
            )
            logger.debug(
                "Applied edit to '%s' (%s match)",
                edit.section_id,
                match_type.value,
            )
        else:
            skipped.append(
                SkippedEdit(
                    section_id=edit.section_id,
                    edit_type=edit.edit_type,
                    reason=(
                        f"Could not locate original_text in section "
                        f"'{edit.section_id}'. Text may have been "
                        f"paraphrased by the LLM or spans complex "
                        f"nested markup."
                    ),
                )
            )
            logger.debug(
                "Skipped edit for '%s' — no text match found",
                edit.section_id,
            )

    modified_html = str(soup)

    logger.info(
        "Rendering complete: %d applied, %d skipped (of %d total)",
        len(applied),
        len(skipped),
        len(edits),
    )

    return modified_html, applied, skipped


# ── Section resolution ─────────────────────────────────────────────────────────


def _resolve_section(
    soup: BeautifulSoup,
    section: PageSection,
) -> Optional[Tag]:
    """
    Locate a section element in the DOM using its CSS selector.

    Falls back to searching by ``section_id`` as an HTML ``id`` attribute
    if the CSS selector fails.

    Returns ``None`` if the element cannot be found.
    """
    # Primary: CSS selector.
    try:
        element = soup.select_one(section.css_selector)
        if element is not None:
            return element
    except Exception:
        # Invalid CSS selector — fall through to fallback.
        logger.debug(
            "CSS selector '%s' failed for section '%s', trying fallback",
            section.css_selector,
            section.section_id,
        )

    # Fallback: try matching by id attribute if the selector was id-based.
    if section.css_selector.startswith("#"):
        el_id = section.css_selector[1:]
        element = soup.find(id=el_id)
        if element is not None and isinstance(element, Tag):
            return element

    return None


# ── Text replacement engine ───────────────────────────────────────────────────


def _select_replacement_target(
    section_element: Tag,
    original_text: str,
) -> Optional[Tag]:
    """
    Find the safest DOM node inside a section to rewrite.

    Broad section wrappers often contain many unrelated text blocks
    (menus, product cards, FAQ lists). Replacing across the whole subtree
    can inject the new copy into the first nested text node. Instead, we
    search for the smallest safe descendant whose visible text matches the
    edit's ``original_text``.
    """
    norm_original = _normalize_whitespace(original_text)
    if not norm_original:
        return None

    candidates: list[tuple[tuple[int, int, int, int], Tag]] = []

    for candidate in _iter_candidate_elements(section_element):
        candidate_text = _extract_visible_text(candidate)
        if not candidate_text:
            continue

        norm_candidate = _normalize_whitespace(candidate_text)
        if not norm_candidate:
            continue

        if norm_candidate == norm_original:
            match_kind = 0
        elif norm_original in norm_candidate:
            coverage = len(norm_original) / max(len(norm_candidate), 1)
            if coverage < 0.72:
                continue
            match_kind = 1
        else:
            continue

        if not _is_safe_target_candidate(
            candidate=candidate,
            section_element=section_element,
            visible_text=candidate_text,
        ):
            continue

        candidates.append(
            (
                (
                    match_kind,
                    1 if candidate is section_element else 0,
                    abs(len(candidate_text) - len(original_text)),
                    -_depth_from_root(candidate, section_element),
                ),
                candidate,
            )
        )

    if not candidates:
        return None

    return min(candidates, key=lambda item: item[0])[1]


def _iter_candidate_elements(section_element: Tag):
    """Yield the section element and all visible descendant tags."""
    yield section_element

    for candidate in section_element.find_all(True):
        if candidate.name in _SKIP_TAGS:
            continue
        yield candidate


def _is_safe_target_candidate(
    *,
    candidate: Tag,
    section_element: Tag,
    visible_text: str,
) -> bool:
    """
    Reject targets that are likely to be structural wrappers or component chrome.
    """
    text_len = len(visible_text)

    # Long text nested inside a button/link is usually component boilerplate,
    # not a user-facing copy block we should rewrite wholesale.
    if text_len > 80 and _has_interactive_ancestor(candidate, stop_at=section_element):
        return False

    # Large containers with multiple substantial child blocks are too broad to
    # rewrite as one contiguous string.
    if text_len > 40 and _is_composite_container(candidate):
        return False

    return True


def _has_interactive_ancestor(candidate: Tag, *, stop_at: Tag) -> bool:
    """Check whether the node lives inside an interactive container."""
    current: Optional[Tag] = candidate
    while current is not None:
        if current.name in _INTERACTIVE_TAGS:
            return True
        if current is stop_at:
            break
        parent = current.parent
        current = parent if isinstance(parent, Tag) else None
    return False


def _is_composite_container(element: Tag) -> bool:
    """
    Heuristic: containers with multiple substantial descendant text blocks are
    structural wrappers, not single rewriteable text blocks.
    """
    parent_text = _extract_visible_text(element)
    parent_norm = _normalize_whitespace(parent_text)
    if len(parent_norm) < 40:
        return False

    meaningful_children = 0
    for child in element.find_all(True):
        if child is element:
            continue
        if child.name in _SKIP_TAGS:
            continue
        if child.name not in _BLOCK_TAGS:
            continue

        child_text = _extract_visible_text(child)
        child_norm = _normalize_whitespace(child_text)
        if len(child_norm) < 20:
            continue

        coverage = len(child_norm) / max(len(parent_norm), 1)
        if 0.12 <= coverage < 0.9:
            meaningful_children += 1
            if meaningful_children >= 2:
                return True

    return False


def _depth_from_root(candidate: Tag, root: Tag) -> int:
    """Return descendant depth relative to a section root."""
    depth = 0
    current: Optional[Tag] = candidate
    while current is not None and current is not root:
        parent = current.parent
        current = parent if isinstance(parent, Tag) else None
        depth += 1
    return depth


def _apply_text_replacement(
    element: Tag,
    original_text: str,
    replacement_text: str,
    *,
    enable_fuzzy: bool = True,
) -> Optional[MatchType]:
    """
    Replace ``original_text`` with ``replacement_text`` inside ``element``.

    Uses a dual-pass approach:
      Pass 1 — Exact substring match.
      Pass 2 — Whitespace-normalised fuzzy match.

    Returns the ``MatchType`` on success, or ``None`` if no match is found.
    """
    # Collect all text nodes in the subtree.
    text_nodes = _collect_text_nodes(element)
    if not text_nodes:
        return None

    # Pass 1: exact match.
    if _try_replace_in_nodes(text_nodes, original_text, replacement_text):
        return MatchType.EXACT

    # Pass 2: fuzzy match (normalised whitespace).
    if enable_fuzzy:
        norm_original = _normalize_whitespace(original_text)
        if norm_original and _try_replace_normalized(
            text_nodes, norm_original, replacement_text,
        ):
            return MatchType.FUZZY

    return None


def _try_replace_in_nodes(
    text_nodes: list[NavigableString],
    original: str,
    replacement: str,
) -> bool:
    """
    Attempt exact-match replacement across a list of text nodes.

    Concatenates all text nodes, finds the ``original`` substring,
    then maps the match back to individual text nodes and replaces
    their content.
    """
    # Concatenate all text node content.
    concatenated = "".join(str(node) for node in text_nodes)

    start_idx = concatenated.find(original)
    if start_idx < 0:
        return False

    end_idx = start_idx + len(original)

    _replace_across_nodes(text_nodes, start_idx, end_idx, replacement)
    return True


def _try_replace_normalized(
    text_nodes: list[NavigableString],
    norm_original: str,
    replacement: str,
) -> bool:
    """
    Attempt whitespace-normalised replacement across text nodes.

    Normalises both the concatenated text and the original,
    finds the match in normalised space, then maps back to the
    raw text nodes.
    """
    # Build raw concatenation and its normalised form.
    raw_parts: list[str] = [str(node) for node in text_nodes]
    raw_concat = "".join(raw_parts)
    norm_concat = _normalize_whitespace(raw_concat)

    norm_start = norm_concat.find(norm_original)
    if norm_start < 0:
        return False

    norm_end = norm_start + len(norm_original)

    # Map normalised indices back to raw indices.
    raw_start = _map_norm_index_to_raw(raw_concat, norm_start)
    raw_end = _map_norm_index_to_raw(raw_concat, norm_end)

    if raw_start is None or raw_end is None:
        return False

    _replace_across_nodes(text_nodes, raw_start, raw_end, replacement)
    return True


def _replace_across_nodes(
    text_nodes: list[NavigableString],
    start_idx: int,
    end_idx: int,
    replacement: str,
) -> None:
    """
    Replace a character range [start_idx, end_idx) across multiple
    text nodes with ``replacement``.

    The replacement text is placed entirely in the first affected node.
    Text nodes fully consumed by the range are emptied.  The last
    affected node keeps its trailing content.
    """
    offset = 0

    for node in text_nodes:
        node_text = str(node)
        node_start = offset
        node_end = offset + len(node_text)

        if node_end <= start_idx or node_start >= end_idx:
            # This node is entirely outside the replacement range.
            offset = node_end
            continue

        # Calculate the overlap within this node.
        local_start = max(0, start_idx - node_start)
        local_end = min(len(node_text), end_idx - node_start)

        # Build the new text for this node.
        if node_start <= start_idx:
            # This is the first affected node — insert the replacement.
            new_text = (
                node_text[:local_start]
                + replacement
                + node_text[local_end:]
            )
            # Only insert replacement once — subsequent nodes that
            # overlap the range just have their matched portion removed.
            replacement = ""
        else:
            # Subsequent affected nodes — just remove the matched portion.
            new_text = node_text[:local_start] + node_text[local_end:]

        node.replace_with(NavigableString(new_text))

        offset = node_end


# ── Text node collection ──────────────────────────────────────────────────────


def _collect_text_nodes(element: Tag) -> list[NavigableString]:
    """
    Collect all visible text nodes in the subtree of ``element``.

    Skips text inside ``<script>``, ``<style>``, and similar non-visible
    tags.  Includes text inside inline formatting tags (``<em>``,
    ``<strong>``, etc.) since those are part of the logical text block.
    """
    nodes: list[NavigableString] = []
    _walk_for_text(element, nodes)
    return nodes


def _walk_for_text(
    element: Tag,
    nodes: list[NavigableString],
) -> None:
    """Recursively collect NavigableString nodes, skipping non-visible tags."""
    for child in element.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            # Skip empty-ish strings and comments.
            if _strip_invisible_chars(str(child)).strip():
                nodes.append(child)
        elif isinstance(child, Tag):
            if child.name in _SKIP_TAGS:
                continue
            _walk_for_text(child, nodes)


# ── Whitespace normalisation ──────────────────────────────────────────────────


_WHITESPACE_RE = re.compile(r"\s+")
_INVISIBLE_CHAR_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_IGNORABLE_CHAR_RE = re.compile(r"[\s\u200b\u200c\u200d\ufeff]")


def _strip_invisible_chars(text: str) -> str:
    """Remove zero-width guard characters inserted by some site builders."""
    return _INVISIBLE_CHAR_RE.sub("", text)


def _normalize_whitespace(text: str) -> str:
    """Aggressively remove ALL whitespace to guarantee alignment across text-node gaps."""
    text = _strip_invisible_chars(text)
    return _WHITESPACE_RE.sub("", text)


def _extract_visible_text(element: Tag) -> str:
    """Return human-readable visible text for candidate ranking."""
    text_nodes = _collect_text_nodes(element)
    if not text_nodes:
        return ""
    parts = [
        _WHITESPACE_RE.sub(" ", _strip_invisible_chars(str(node))).strip()
        for node in text_nodes
    ]
    return " ".join(part for part in parts if part)


def _map_norm_index_to_raw(raw_text: str, norm_index: int) -> Optional[int]:
    """
    Map a character index in whitespace-stripped text back to the corresponding
    index in the raw text.
    """
    norm_pos = 0

    for raw_pos, ch in enumerate(raw_text):
        if norm_pos == norm_index:
            return raw_pos

        # If it's a visible, non-ignorable character, increment the stripped
        # index used by fuzzy matching.
        if not _IGNORABLE_CHAR_RE.fullmatch(ch):
            norm_pos += 1

    # If norm_index equals the length of normalised text, return
    # the end of the text.
    if norm_pos == norm_index:
        return len(raw_text)

    return None
