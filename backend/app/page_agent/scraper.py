"""
Landing Page Scraper — HTTP fetch + BeautifulSoup section parser.

Responsible for:
  1. Fetching raw HTML from a landing page URL.
  2. Parsing the HTML into labeled ``PageSection`` objects using a
     **top-down recursive walk** that produces non-overlapping sections.

This module is **purely deterministic** — no LLM calls.

Design note:
  The parser walks down from ``<body>`` and captures the first meaningful
  element it finds on each branch, then stops recursing into that subtree.
  This guarantees non-overlapping sections (a section's children are never
  captured separately) and keeps the section count to ~5–20 per page,
  regardless of DOM depth.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

from app.page_agent.schemas import PageSection, PageStructure, SectionType

logger = logging.getLogger(__name__)

# ── Tuning constants ───────────────────────────────────────────────────────────

# Minimum visible-text length for an element to be captured as a section.
_MIN_SECTION_TEXT_LEN = 20

# Hard cap on sections per page.  Even complex pages rarely need more than 20.
_MAX_SECTIONS = 20

# Maximum HTML chars stored per section (for Step 4 renderer).
_MAX_SECTION_HTML_LEN = 50_000

# Realistic browser User-Agent to avoid bot-blocking.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ── Tag classification sets ────────────────────────────────────────────────────

# Tags that are never sections and never recursed into.
_NOISE_TAGS: frozenset[str] = frozenset({
    "script", "style", "noscript", "link", "meta", "br", "hr",
    "img", "input", "svg", "path", "iframe", "head", "template",
})

# Semantic HTML5 tags that are always captured as a section (stop recursing).
_SEMANTIC_SECTION_TAGS: frozenset[str] = frozenset({
    "section", "header", "footer", "nav", "aside", "article",
})

# Container tags that should be *recursed into*, not captured as a section.
_CONTAINER_TAGS: frozenset[str] = frozenset({
    "main", "body", "form", "fieldset",
})

# ── Class/ID → SectionType pattern map ─────────────────────────────────────────

_PATTERN_MAP: list[tuple[re.Pattern[str], SectionType]] = [
    (re.compile(r"hero", re.IGNORECASE), SectionType.HERO),
    (re.compile(r"banner", re.IGNORECASE), SectionType.HERO),
    (re.compile(r"jumbotron", re.IGNORECASE), SectionType.HERO),
    (re.compile(r"cta|call.?to.?action", re.IGNORECASE), SectionType.CTA),
    (re.compile(r"benefit", re.IGNORECASE), SectionType.BENEFITS),
    (re.compile(r"feature", re.IGNORECASE), SectionType.FEATURES),
    (re.compile(r"testimonial|review|quote", re.IGNORECASE), SectionType.TESTIMONIALS),
    (re.compile(r"trust|social.?proof|logo.?bar|partner", re.IGNORECASE), SectionType.TRUST_SIGNALS),
    (re.compile(r"pricing|plan", re.IGNORECASE), SectionType.PRICING),
    (re.compile(r"faq|question|accordion", re.IGNORECASE), SectionType.FAQ),
    (re.compile(r"nav|menu|navbar", re.IGNORECASE), SectionType.NAVIGATION),
    (re.compile(r"foot", re.IGNORECASE), SectionType.FOOTER),
]

# CTA button text patterns (used for content-based classification).
_CTA_TEXT_PATTERN = re.compile(
    r"(sign.?up|get.?started|buy.?now|shop.?now|try.?free|start|subscribe|learn.?more)",
    re.IGNORECASE,
)

_INVISIBLE_CHAR_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_WHITESPACE_RE = re.compile(r"\s+")


# ── Public API ─────────────────────────────────────────────────────────────────


async def scrape_landing_page(url: str) -> PageStructure:
    """
    Fetch a landing page and parse it into a structured ``PageStructure``.

    Args:
        url: The landing page URL to scrape.

    Returns:
        ``PageStructure`` containing raw HTML, metadata, and labeled sections.

    Raises:
        httpx.HTTPStatusError: If the page returns a non-2xx status.
        ValueError: If no meaningful content could be extracted.
    """
    raw_html = await _fetch_page(url)
    soup = BeautifulSoup(raw_html, "html.parser")

    # Extract metadata
    title = _extract_title(soup)
    meta_description = _extract_meta_description(soup)

    # Parse sections via top-down recursive walk
    sections = _parse_sections(soup)

    if not sections:
        shell_reason = _detect_client_rendered_shell(soup)
        if shell_reason:
            logger.info(
                "Plain HTTP fetch returned a client-rendered shell for %s — "
                "trying browser-rendered fallback",
                url,
            )

            rendered_html = await _fetch_page_rendered(url)
            if rendered_html:
                raw_html = rendered_html
                soup = BeautifulSoup(raw_html, "html.parser")
                title = _extract_title(soup)
                meta_description = _extract_meta_description(soup)
                sections = _parse_sections(soup)

            if not sections:
                raise ValueError(
                    "Fetched HTML contains only a client-rendered app shell, "
                    f"not real landing-page copy. {shell_reason}"
                )

        if not sections:
            logger.warning(
                "No meaningful sections detected on %s — "
                "page may use non-standard markup",
                url,
            )

    logger.info(
        "Scraped %s — title=%r, %d sections detected",
        url,
        title,
        len(sections),
    )

    # Inject a <base> tag so that relative assets (CSS, JS, images) load correctly
    # when the HTML is saved and viewed as a local file.
    if not soup.find("base"):
        base_tag = soup.new_tag("base", href=url)
        if soup.head:
            soup.head.insert(0, base_tag)
        elif html_tag := soup.find("html"):
            html_tag.insert(0, base_tag)
        raw_html = str(soup)

    return PageStructure(
        url=url,
        title=title,
        meta_description=meta_description,
        raw_html=raw_html,
        sections=sections,
    )


# ── HTTP fetch ─────────────────────────────────────────────────────────────────


async def _fetch_page(url: str) -> str:
    """
    Fetch raw HTML from a URL.

    Uses a realistic User-Agent, follows HTTP 3xx redirects (not page links),
    and raises on non-2xx.
    """
    async with httpx.AsyncClient(
        timeout=25.0,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    logger.debug("Fetched %s — %d bytes, status %d", url, len(resp.text), resp.status_code)
    return resp.text


async def _fetch_page_rendered(url: str) -> Optional[str]:
    """
    Render a JS-heavy page in a real browser and return the post-hydration HTML.

    This is an automatic fallback for SPA shells where the plain HTTP response
    contains an empty root element and no user-facing copy.
    """
    try:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning(
            "Browser-rendered fallback unavailable for %s — playwright is not installed",
            url,
        )
        return None

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=_USER_AGENT,
                viewport={"width": 1440, "height": 900},
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            try:
                await page.wait_for_function(
                    """
                    () => (
                        document.body &&
                        document.body.innerText &&
                        document.body.innerText.trim().length > 120
                    )
                    """,
                    timeout=15_000,
                )
            except PlaywrightTimeoutError:
                # Some pages never become fully idle due to analytics, chat
                # widgets, or long-polling. If the DOM is already loaded, we
                # still capture the current rendered HTML after a short pause.
                await page.wait_for_timeout(2_000)
            html = await page.content()
            logger.info(
                "Browser-rendered fallback succeeded for %s — %d bytes",
                url,
                len(html),
            )
            return html
    except PlaywrightTimeoutError:
        logger.warning(
            "Browser-rendered fallback timed out for %s",
            url,
        )
        return None
    except Exception as exc:
        logger.warning(
            "Browser-rendered fallback failed for %s: %s: %s",
            url,
            type(exc).__name__,
            exc,
        )
        return None
    finally:
        if browser is not None:
            await browser.close()


# ── Metadata extraction ───────────────────────────────────────────────────────


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract the <title> tag content."""
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else None


def _extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract the <meta name='description'> content."""
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and isinstance(tag, Tag):
        content = tag.get("content")
        if isinstance(content, str):
            return content.strip() or None
    return None


# ── Section parsing — top-down recursive walk ──────────────────────────────────


def _parse_sections(soup: BeautifulSoup) -> list[PageSection]:
    """
    Parse a landing page into non-overlapping labeled sections.

    Uses a **top-down recursive walk** from ``<body>``:
      • If an element is recognisable (semantic tag or known class/id),
        capture it as a section and **stop** — don't recurse into its children.
      • If an element is a generic container (``<div>`` with no known class,
        ``<main>``, etc.), recurse into its children.
      • Noise elements (``<script>``, ``<style>``, etc.) are skipped entirely.

    Falls back to capturing direct ``<body>`` children if the recursive
    walk finds nothing (pages with no semantic markup at all).
    """
    sections: list[PageSection] = []
    counters: dict[str, int] = {}

    body = soup.find("body")
    if not body or not isinstance(body, Tag):
        return sections

    _walk_and_collect(body, counters, sections)

    # Fallback: if the walk found nothing, capture direct body children.
    if not sections:
        for child in body.children:
            if len(sections) >= _MAX_SECTIONS:
                break
            if not isinstance(child, Tag):
                continue
            if child.name in _NOISE_TAGS:
                continue
            section = _element_to_section(child, counters)
            if section:
                sections.append(section)

    return sections


def _walk_and_collect(
    parent: Tag,
    counters: dict[str, int],
    sections: list[PageSection],
) -> None:
    """
    Recursively walk children of ``parent`` and collect non-overlapping sections.

    When an element is captured as a section, its entire subtree is skipped
    (no child is captured separately).  This guarantees zero overlap.
    """
    for child in parent.children:
        if len(sections) >= _MAX_SECTIONS:
            return

        if not isinstance(child, Tag):
            continue

        # Skip noise
        if child.name in _NOISE_TAGS:
            continue

        # Decide: capture as section, or recurse into it?
        if _is_meaningful_section(child):
            section = _element_to_section(child, counters)
            if section:
                sections.append(section)
            # Stop — don't recurse into this subtree.
        else:
            # Generic container — recurse into its children.
            _walk_and_collect(child, counters, sections)


def _is_meaningful_section(element: Tag) -> bool:
    """
    Determine whether an element should be captured as a discrete section.

    Returns ``True`` for:
      • Semantic HTML5 section tags (``<section>``, ``<header>``, etc.)
      • Elements whose class/id matches a known pattern
      • ``<div>`` elements with a heading child AND enough content
    Returns ``False`` for:
      • Container tags (``<main>``, ``<body>``, ``<form>``)
      • ``<div>`` elements with no recognisable class/id and no heading
    """
    # Container tags are never captured — always recursed into.
    if element.name in _CONTAINER_TAGS:
        return False

    # Semantic HTML5 section tags are always captured.
    if element.name in _SEMANTIC_SECTION_TAGS:
        return True

    # For <div> and other tags: check class/id for known patterns.
    class_id_text = _get_class_id_text(element)
    if class_id_text:
        for pattern, _ in _PATTERN_MAP:
            if pattern.search(class_id_text):
                return True

    # Heuristic: a <div> with a heading child and decent text is likely
    # a standalone content block.  Capture it instead of recursing.
    if element.name == "div":
        has_heading = bool(element.find(["h1", "h2", "h3"], recursive=False))
        text_len = len(element.get_text(strip=True))
        if has_heading and text_len >= 50:
            return True

    return False


# ── Element → PageSection conversion ──────────────────────────────────────────


def _element_to_section(
    element: Tag,
    counters: dict[str, int],
) -> Optional[PageSection]:
    """
    Convert a BeautifulSoup ``Tag`` into a ``PageSection``.

    Returns ``None`` if the element has insufficient visible text.
    """
    text_content = _extract_visible_text(element)
    if len(text_content) < _MIN_SECTION_TEXT_LEN:
        return None

    section_type = _classify_element(element)
    type_key = section_type.value
    idx = counters.get(type_key, 0)
    counters[type_key] = idx + 1

    section_id = f"{type_key}_{idx}"
    css_selector = _build_css_selector(element)

    # Truncate HTML content to keep payloads reasonable for Step 4 renderer.
    html_content = str(element)
    if len(html_content) > _MAX_SECTION_HTML_LEN:
        html_content = html_content[:_MAX_SECTION_HTML_LEN] + "<!-- truncated -->"

    return PageSection(
        section_id=section_id,
        section_type=section_type,
        css_selector=css_selector,
        html_content=html_content,
        text_content=text_content,
    )


def _classify_element(element: Tag) -> SectionType:
    """
    Classify an element into a ``SectionType``.

    Priority: tag name → class/id pattern → content heuristic → OTHER.
    """
    # ── Tag-name based classification ──
    _tag_map: dict[str, SectionType] = {
        "header": SectionType.NAVIGATION,
        "nav": SectionType.NAVIGATION,
        "footer": SectionType.FOOTER,
    }
    if element.name in _tag_map:
        return _tag_map[element.name]

    # ── Class/ID pattern matching ──
    class_id_text = _get_class_id_text(element)
    if class_id_text:
        for pattern, section_type in _PATTERN_MAP:
            if pattern.search(class_id_text):
                return section_type

    # ── Content-based heuristics ──

    # Short element with a heading → headline
    h_tags = element.find_all(["h1", "h2"], limit=2)
    if h_tags and len(element.get_text(strip=True)) < 200:
        return SectionType.HEADLINE

    # Element with CTA-like button text → CTA
    for btn in element.find_all(["button", "a"], limit=5):
        if _CTA_TEXT_PATTERN.search(btn.get_text(strip=True)):
            return SectionType.CTA

    return SectionType.OTHER


# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_class_id_text(element: Tag) -> str:
    """Concatenate the element's class and id attributes into a single string."""
    parts: list[str] = []

    classes = element.get("class", [])
    if isinstance(classes, list):
        parts.extend(classes)
    elif isinstance(classes, str):
        parts.append(classes)

    el_id = element.get("id", "")
    if isinstance(el_id, str) and el_id:
        parts.append(el_id)

    return " ".join(parts)


def _extract_visible_text(element: Tag) -> str:
    """Extract visible text while stripping zero-width builder guard chars."""
    raw_text = element.get_text(separator=" ", strip=True)
    raw_text = _INVISIBLE_CHAR_RE.sub("", raw_text)
    return _WHITESPACE_RE.sub(" ", raw_text).strip()


def _detect_client_rendered_shell(soup: BeautifulSoup) -> Optional[str]:
    """
    Detect pages where the HTTP response contains only an empty SPA shell.

    These pages need a browser-rendered fetch path; plain HTTP scraping
    cannot see the actual user-facing copy.
    """
    body = soup.find("body")
    if not body or not isinstance(body, Tag):
        return None

    root_ids = ("root", "__next", "app", "__nuxt", "gatsby")
    root = next(
        (
            el for root_id in root_ids
            if (el := body.find(id=root_id)) and isinstance(el, Tag)
        ),
        None,
    )
    if root is None:
        return None

    root_text = _extract_visible_text(root)
    if root_text:
        return None

    module_scripts = soup.find_all("script", attrs={"type": "module"})
    script_srcs = [
        script.get("src", "")
        for script in soup.find_all("script", src=True)
        if isinstance(script, Tag)
    ]
    has_framework_bootstrap = any(
        token in src.lower()
        for src in script_srcs
        for token in ("/assets/", "main-", "vendor-", "chunk", "_next", "gatsby")
    )

    if module_scripts or has_framework_bootstrap:
        return (
            f"Found empty '#{root.get('id')}' root plus client-side JS bundles. "
            "This URL needs browser rendering (for example Playwright/Selenium) "
            "or an SSR/static HTML version before personalization can run."
        )

    return None


def _build_css_selector(element: Tag) -> str:
    """
    Build a CSS selector path for an element.

    Prefers id-based selectors, then class-based, then positional.
    """
    el_id = element.get("id", "")
    if isinstance(el_id, str) and el_id:
        return f"#{el_id}"

    classes = element.get("class", [])
    if isinstance(classes, list) and classes:
        class_selector = ".".join(classes)
        return f"{element.name}.{class_selector}"

    # Positional: tag name + nth-of-type
    if element.parent and isinstance(element.parent, Tag):
        siblings = [
            s for s in element.parent.children
            if isinstance(s, Tag) and s.name == element.name
        ]
        if len(siblings) > 1:
            idx = siblings.index(element) + 1
            return f"{element.name}:nth-of-type({idx})"

    return element.name or "div"
