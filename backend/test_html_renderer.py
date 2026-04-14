from app.edit_agent.schemas import EditType, SectionEdit
from app.page_agent.schemas import PageSection, SectionType
from app.renderer.html_renderer import render_edits


def test_renderer_rewrites_simple_heading():
    raw_html = """
    <div id="hero_0" class="hero">
        <h1>Transform Your <em>Business</em> Today</h1>
        <p>This is some content! Join 10,000 customers.</p>
    </div>
    """

    sections = [
        PageSection(
            section_id="hero_0",
            section_type=SectionType.HERO,
            css_selector="#hero_0",
            html_content=raw_html,
            text_content="Transform Your Business Today This is some content! Join 10,000 customers.",
        )
    ]

    edits = [
        SectionEdit(
            section_id="hero_0",
            edit_type=EditType.HEADLINE_REWRITE,
            original_text="Transform Your Business Today",
            replacement_text="Scale Your Enterprise Tomorrow",
            reasoning="Testing",
            confidence=0.9,
        )
    ]

    modified_html, applied, skipped = render_edits(
        raw_html,
        edits,
        sections,
        enable_fuzzy=True,
    )

    assert len(applied) == 1
    assert len(skipped) == 0
    assert "Scale Your Enterprise Tomorrow" in modified_html


def test_renderer_ignores_zero_width_builder_guards():
    raw_html = """
    <section id="headline_0">
        <h2><span>\u200b</span>Follow us on Instagram</h2>
        <p><span>\u200b</span>Load more</p>
    </section>
    """

    sections = [
        PageSection(
            section_id="headline_0",
            section_type=SectionType.HEADLINE,
            css_selector="#headline_0",
            html_content=raw_html,
            text_content="Follow us on Instagram Load more",
        )
    ]

    edits = [
        SectionEdit(
            section_id="headline_0",
            edit_type=EditType.HEADLINE_REWRITE,
            original_text="Follow us on Instagram",
            replacement_text="See the upcycled denim collection in action",
            reasoning="Testing zero-width guard handling",
            confidence=0.82,
        )
    ]

    modified_html, applied, skipped = render_edits(
        raw_html,
        edits,
        sections,
        enable_fuzzy=True,
    )

    assert len(applied) == 1
    assert len(skipped) == 0
    assert "See the upcycled denim collection in action" in modified_html


def test_renderer_skips_composite_wrapper_rewrite():
    raw_html = """
    <section id="products">
        <div class="card">
            <button><span>Add to Cart Brick Bag Sale Price 840</span></button>
        </div>
        <div class="card">
            <button><span>Add to Cart Messenger Bag Sale Price 1000</span></button>
        </div>
    </section>
    """

    sections = [
        PageSection(
            section_id="other_0",
            section_type=SectionType.OTHER,
            css_selector="#products",
            html_content=raw_html,
            text_content=(
                "Add to Cart Brick Bag Sale Price 840 "
                "Add to Cart Messenger Bag Sale Price 1000"
            ),
        )
    ]

    edits = [
        SectionEdit(
            section_id="other_0",
            edit_type=EditType.BODY_REWRITE,
            original_text=(
                "Add to Cart Brick Bag Sale Price 840 "
                "Add to Cart Messenger Bag Sale Price 1000"
            ),
            replacement_text="Shop handcrafted upcycled denim bags designed to stand out.",
            reasoning="This should not be applied into the first nested button.",
            confidence=0.75,
        )
    ]

    modified_html, applied, skipped = render_edits(
        raw_html,
        edits,
        sections,
        enable_fuzzy=True,
    )

    assert len(applied) == 0
    assert len(skipped) == 1
    assert "safe DOM target" in skipped[0].reason
    assert "Shop handcrafted upcycled denim bags designed to stand out." not in modified_html
    assert "Add to Cart Brick Bag Sale Price 840" in modified_html
    assert "Add to Cart Messenger Bag Sale Price 1000" in modified_html
