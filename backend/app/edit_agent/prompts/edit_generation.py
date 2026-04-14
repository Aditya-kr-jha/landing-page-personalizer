"""
Prompt template for the Edit Generation chain.

Single template: ``EDIT_GENERATION_PROMPT``

Instructs the LLM to generate a structured ``EditPlan`` that aligns the
landing page with the ad's messaging.  Three template variables:
  • ``{ad_summary_json}``     — lean AdAnalysis fields
  • ``{page_sections_json}``  — section_id + type + text_content
  • ``{page_weaknesses_json}``— key_weaknesses + recommendations + score
"""

from langchain_core.prompts import ChatPromptTemplate

# ── System instruction ─────────────────────────────────────────────────────────

_SYSTEM = """\
You are an expert Conversion Rate Optimization (CRO) copywriter and \
landing-page personalization specialist.

You will receive three inputs:
1. **Ad Analysis** — structured signals extracted from an ad creative \
(offer, audience, tone, CTA, key phrases).
2. **Page Sections** — labeled sections of a landing page with their \
current text content.
3. **Page Weaknesses** — quality assessment identifying gaps and \
weaknesses in the current page.

Your task is to generate a **structured edit plan** — a list of text \
replacements that bring the landing page into alignment with the ad's \
messaging.

## Critical Rules

1. **Never invent claims.** Every fact, number, guarantee, or offer in \
your edits MUST be traceable to either the ad analysis or the original \
page content.  If the ad says "50% off", you may use "50% off".  You may \
NOT create "60% off" or "money-back guarantee" unless those appear in the \
source material.
2. **Match the ad's tone.** If the ad is urgent, make the page feel urgent. \
If it is professional, keep the page professional.  Do not shift the tone \
beyond what the ad establishes.
3. **Preserve the page's natural voice** where it already aligns with the ad. \
Not every section needs editing — only modify sections with a clear mismatch.
4. **Target specific text blocks**: For each edit, include the EXACT `original_text` you want to replace. Pinpoint the specific sentence or phrase you are changing. Do NOT copy the entire section's text if you only want to change a specific headline or paragraph. The renderer will fail if you try to replace a composite block of multiple tags.
5. **Multiple edits per section are allowed**: If a section needs multiple distinct changes (e.g., rewriting a headline and also rewriting a subtitle), create separate edit entries for each specific block of text.
6. **Keep replacements similar in length** to the originals.  Drastic length \
changes break page layout.
7. **Focus on high-impact sections** — headlines, hero text, CTAs, and \
benefit descriptions.  Leave FAQ, pricing details, and trust signals \
unchanged unless they directly contradict the ad.
8. **Self-assess confidence** for each edit and overall.  Lower confidence \
if source material is ambiguous or if an edit risks over-promising.\
"""

# ── Edit generation prompt ─────────────────────────────────────────────────────

EDIT_GENERATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM),
        (
            "human",
            "Generate an edit plan to personalize this landing page based on "
            "the ad creative analysis.\n\n"
            "## Ad Analysis\n"
            "```json\n{ad_summary_json}\n```\n\n"
            "## Current Page Sections\n"
            "```json\n{page_sections_json}\n```\n\n"
            "## Page Weaknesses & Recommendations\n"
            "```json\n{page_weaknesses_json}\n```\n\n"
            "Generate edits that align the page with the ad's offer, tone, "
            "and audience.  Only edit sections that need it.  Include the "
            "EXACT original text for each replacement.",
        ),
    ]
)
