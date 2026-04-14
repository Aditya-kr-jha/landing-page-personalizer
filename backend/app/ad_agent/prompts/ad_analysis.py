"""
Prompt templates for the Ad Analysis chain.

Two variants:
  • IMAGE_ANALYSIS_PROMPT  — multimodal (image + instruction) for GPT-4o vision.
  • TEXT_ANALYSIS_PROMPT   — text-only fallback for scraped ad pages.

Both share a system instruction enforcing CRO-focused analysis.
"""

from langchain_core.prompts import ChatPromptTemplate

# ── Shared system instruction ──────────────────────────────────────────────────

_SYSTEM = """\
You are an expert advertising analyst and Conversion Rate Optimization (CRO) \
specialist.

Your task is to deeply analyze an ad creative and extract structured messaging \
signals that will later be used to personalize a landing page for better \
conversion.

## Analysis Principles

1. **Be specific** — never say "good product"; say "protein powder for \
first-time buyers".
2. **Infer the audience** — even if the ad doesn't state it explicitly, deduce \
it from imagery, language, and context.
3. **Capture the EXACT offer** — if the ad says "50% off", report "50% off", \
not "discount".
4. **Note urgency cues** — countdown timers, "limited time", "only X left", etc.
5. **Describe visuals** — colors, imagery style, layout direction. These inform \
the landing-page personalization.
6. **Extract ALL text** — OCR every piece of text visible on the creative and \
return it in `raw_text_extracted`.
7. **Self-assess confidence** — if the image is blurry or the ad is ambiguous, \
lower your confidence score and note warnings.\
"""

# ── Image analysis (multimodal) ────────────────────────────────────────────────

IMAGE_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM),
        (
            "human",
            [
                {
                    "type": "text",
                    "text": (
                        "Analyze the following ad creative image.\n\n"
                        "Extract every piece of messaging: headline, offer, CTA, "
                        "audience, tone, urgency, trust signals, and visual "
                        "description.\n\n"
                        "Be thorough and specific."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "{image_url}"},
                },
            ],
        ),
    ]
)

# ── Text-only analysis (scraped ad page) ───────────────────────────────────────

TEXT_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM),
        (
            "human",
            "The following text was extracted from an ad page or ad listing.\n"
            "Analyze it as an ad creative and extract structured messaging "
            "signals.\n\n"
            "--- START OF AD TEXT ---\n"
            "{ad_text}\n"
            "--- END OF AD TEXT ---",
        ),
    ]
)
