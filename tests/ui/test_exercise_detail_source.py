"""UI: exercise detail shows the source scenario (with link) and the
renamed Begin Exercise action."""
from __future__ import annotations

import re

from playwright.sync_api import expect

from tests.ui._helpers import seed_exercise

SCENARIO_TITLE = "Linkable Scenario"


def test_begin_exercise_button_label(page, base_url):
    eid = seed_exercise(page, base_url, title=SCENARIO_TITLE, start=False)
    page.goto(f"{base_url}/#exercise={eid}")
    expect(page.get_by_role("button", name=re.compile("Begin Exercise"))).to_be_visible()


def test_source_scenario_link_navigates_to_scenario(page, base_url):
    eid = seed_exercise(page, base_url, title=SCENARIO_TITLE, start=False)
    exercise = page.request.get(f"{base_url}/exercises/{eid}").json()
    scenario = page.request.get(
        f"{base_url}/scenarios/{exercise['scenario_catalog_id']}"
    ).json()
    page.goto(f"{base_url}/#exercise={eid}")
    link = page.get_by_role("link", name=SCENARIO_TITLE)
    expect(link).to_be_visible()
    link.click()
    expect(page.locator("#scenario-detail-content code").filter(
        has_text=scenario["scenario_id"]
    )).to_have_count(1)
