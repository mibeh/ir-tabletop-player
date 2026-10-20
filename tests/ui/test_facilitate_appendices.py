"""UI: the facilitator page surfaces scenario appendix content.

Two appendix sections are facilitator-only reference material:
- ``appendices.facilitator_notes`` renders on inject slides and the hotwash
  slide, beside/below the live panels.
- ``appendices.additional_discussion_questions`` renders on the hotwash slide
  as collapsible sections.
Neither appears on the participant-facing presenter view.
"""
from __future__ import annotations

from playwright.sync_api import expect

from tests.ui._helpers import advance_to, seed_exercise

PITFALL = "Teams often stop at key rotation."
HOTWASH_Q = "Who signs off on customer disclosure?"

APPENDICES = {
    "facilitator_notes": {"common_pitfalls": [PITFALL]},
    "additional_discussion_questions": {
        "Legal": [{"question": HOTWASH_Q, "follow_ups": ["By when?"]}]
    },
}


def test_facilitator_notes_show_on_inject_slide(page, base_url):
    eid = seed_exercise(page, base_url, title="Facilitator Appendix", appendices=APPENDICES)
    advance_to(page, base_url, eid, "inject:0:1")

    page.goto(f"{base_url}/facilitate.html#{eid}")

    expect(page.get_by_text("Common Pitfalls")).to_be_visible()
    expect(page.get_by_text(PITFALL)).to_be_visible()


def test_additional_discussion_questions_expandable_on_hotwash(page, base_url):
    eid = seed_exercise(page, base_url, title="Facilitator Appendix", appendices=APPENDICES)
    advance_to(page, base_url, eid, "hotwash")

    page.goto(f"{base_url}/facilitate.html#{eid}")

    expect(page.get_by_text("Additional discussion questions")).to_be_visible()
    summary = page.locator("details.adq-section summary").filter(has_text="Legal")
    expect(summary).to_be_visible()
    # Collapsed by default: the question is hidden until the section is opened.
    expect(page.get_by_text(HOTWASH_Q)).to_be_hidden()
    summary.click()
    expect(page.get_by_text(HOTWASH_Q)).to_be_visible()


def test_facilitator_notes_show_on_hotwash_slide(page, base_url):
    eid = seed_exercise(page, base_url, title="Facilitator Appendix", appendices=APPENDICES)
    advance_to(page, base_url, eid, "hotwash")

    page.goto(f"{base_url}/facilitate.html#{eid}")

    expect(page.get_by_text("Facilitator tips")).to_be_visible()
    expect(page.get_by_text(PITFALL)).to_be_visible()
