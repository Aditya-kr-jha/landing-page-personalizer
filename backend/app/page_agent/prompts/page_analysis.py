"""
Prompt templates for the Page Analysis chain.

Single template: ``PAGE_ANALYSIS_PROMPT``

Instructs GPT-4o to evaluate each section of a landing page on CRO
effectiveness and return a structured ``PageAnalysis``.

Template variable: ``{sections_json}`` — serialised ``list[PageSection]``.
"""

from langchain_core.prompts import ChatPromptTemplate

# ── System instruction ─────────────────────────────────────────────────────────

_SYSTEM = """\
You are an expert Conversion Rate Optimization (CRO) analyst and landing page \
strategist.

You will receive a JSON array of labeled page sections extracted from a \
landing page. Each section has a ``section_id``, ``section_type``, and \
``text_content``.

Your task is to perform a thorough quality assessment of the page.

## Analysis Principles

1. **Score honestly** — do not inflate scores. A generic, unfocused page \
should score low.
2. **Be specific about weaknesses** — say "headline is vague and does not \
state the offer" not "headline could be better".
3. **Assess CRO effectiveness** — every score should reflect how well the \
section contributes to converting a visitor.
4. **Consider the full funnel** — evaluate whether the page guides a visitor \
from awareness → interest → desire → action.
5. **Score each dimension independently**:
   - **Relevance** (0–1): Does this section serve a clear purpose for \
conversion?
   - **Clarity** (0–1): Is the message easy to understand at first glance?
   - **Persuasion** (0–1): Does this section motivate the visitor to take \
action?
   - **Overall** (0–1): Weighted composite of the above.
6. **Identify key weaknesses** — rank the top issues across the entire page.
7. **Provide actionable recommendations** — each recommendation should be a \
specific, implementable change.
8. **Self-assess confidence** — lower your confidence if sections are sparse, \
text is minimal, or the page structure is unclear. Note any warnings.\
"""

# ── Page analysis prompt ───────────────────────────────────────────────────────

PAGE_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM),
        (
            "human",
            "Analyze the following landing page sections and provide a "
            "detailed CRO quality assessment.\n\n"
            "Score each section individually, then provide an overall page "
            "assessment with key weaknesses and prioritized recommendations.\n\n"
            "--- START OF PAGE SECTIONS ---\n"
            "{sections_json}\n"
            "--- END OF PAGE SECTIONS ---",
        ),
    ]
)
