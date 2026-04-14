import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.renderer.html_renderer import render_edits
from app.edit_agent.schemas import SectionEdit, EditType
from app.page_agent.schemas import PageSection

# HTML that mimics a real landing page structure
html = """
<div id="hero" class="hero-section">
    <h1>
        Welcome to the 
        <span class="highlight">Ad Personalizer</span>
        Platform
    </h1>
    <p>We help you <strong>scale</strong> today.</p>
</div>
"""

sections = [
    PageSection(
        section_id="hero",
        section_type="hero",
        css_selector="#hero",
        html_content=html,
        text_content="Welcome to the Ad Personalizer Platform We help you scale today."
    )
]

edits = [
    SectionEdit(
        section_id="hero",
        edit_type=EditType.HEADLINE_REWRITE,
        original_text="Welcome to the Ad Personalizer Platform",
        replacement_text="Grow your Business with Smart AI",
        confidence=1.0,
        reasoning="Test"
    ),
    SectionEdit(
        section_id="hero",
        edit_type=EditType.HEADLINE_REWRITE,
        original_text="We help you scale today.",
        replacement_text="Achieve 10x ROI instantly.",
        confidence=1.0,
        reasoning="Test"
    )
]

mod_html, applied, skipped = render_edits(html, edits, sections)

print("Applied:", len(applied))
print("Skipped:", len(skipped))
for s in skipped:
    print(f"Skip Reason: {s.reason}")

print("\n--- HTML ---")
print(mod_html)
