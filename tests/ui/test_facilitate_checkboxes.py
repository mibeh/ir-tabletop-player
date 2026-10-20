"""UI: Expected-actions checkboxes reset when moving to the next inject.

Regression test for a lit-html boolean-attribute binding bug: a checked box
bled into the next inject because the ?checked attribute no longer moves a
control once the user has clicked it.
"""
from __future__ import annotations

import re

from playwright.sync_api import expect

from tests.ui._helpers import advance_to, seed_exercise


def test_expected_actions_checkboxes_clear_between_injects(page, base_url):
    eid = seed_exercise(page, base_url, title="Checkbox Scenario")
    advance_to(page, base_url, eid, "inject:0:1")
    page.goto(f"{base_url}/facilitate.html#{eid}")

    first = page.locator(".checks input[type=checkbox]").first
    expect(first).not_to_be_checked()
    first.check()
    expect(first).to_be_checked()

    # Advance to the next inject via the facilitator control.
    page.get_by_role("button", name=re.compile("Next slide")).click()
    expect(page.get_by_text("Action 2.1")).to_be_visible()

    # The reused checkbox must reflect the new inject (unchecked).
    expect(page.locator(".checks input[type=checkbox]").first).not_to_be_checked()
