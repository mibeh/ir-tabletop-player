"""UI: the presenter view is locally browsable once an exercise is complete.

After completion there is no facilitator driving slide navigation, so
present.html switches into a local "browse mode": it starts on the first
slide and exposes Previous/Next controls that page through the whole deck.
"""
from __future__ import annotations

import json

from playwright.sync_api import expect

from tests.factories import make_exercise_payload, make_scenario_json


def _seed_complete_exercise(page, base_url: str) -> str:
    scenario = page.request.post(
        f"{base_url}/scenarios",
        multipart={"files": {
            "name": "s.json",
            "mimeType": "application/json",
            "buffer": json.dumps(
                make_scenario_json(title="Present Browse Source")
            ).encode("utf-8"),
        }},
    ).json()["results"][0]
    ex = page.request.post(
        f"{base_url}/exercises",
        data=json.dumps(make_exercise_payload(
            scenario_catalog_id=scenario["id"],
            title="Present Browse",
        )),
        headers={"content-type": "application/json"},
    ).json()
    eid = ex["exercise_id"]
    page.request.post(f"{base_url}/exercises/{eid}/start")
    for _ in range(200):
        r = page.request.post(f"{base_url}/exercises/{eid}/present/next")
        if not r.ok or r.json().get("status") == "debrief":
            break
    page.request.post(f"{base_url}/exercises/{eid}/complete")
    return eid


def test_complete_exercise_starts_on_first_slide(page, base_url):
    eid = _seed_complete_exercise(page, base_url)
    page.goto(f"{base_url}/present.html#{eid}")

    expect(page.locator(".slide-title")).to_have_text("Before we begin")
    # Default factory deck: ground_rules + 2 modules x (module + 2 injects) + hotwash = 8.
    expect(page.locator("#position")).to_have_text("Ground rules · 1 / 8")


def test_browse_controls_page_through_deck(page, base_url):
    eid = _seed_complete_exercise(page, base_url)
    page.goto(f"{base_url}/present.html#{eid}")

    prev = page.locator("#browse-controls").get_by_role("button", name="Previous")
    nxt = page.locator("#browse-controls").get_by_role("button", name="Next")

    # First slide: cannot go back.
    expect(prev).to_be_disabled()
    expect(nxt).to_be_enabled()

    nxt.click()
    expect(page.locator(".slide-title")).to_have_text("Module 1")
    expect(page.locator("#position")).to_have_text("Module 1 · 2 / 8")
    expect(prev).to_be_enabled()

    prev.click()
    expect(page.locator(".slide-title")).to_have_text("Before we begin")
    expect(prev).to_be_disabled()


def test_next_disabled_on_last_slide(page, base_url):
    eid = _seed_complete_exercise(page, base_url)
    page.goto(f"{base_url}/present.html#{eid}")

    nxt = page.locator("#browse-controls").get_by_role("button", name="Next")
    for _ in range(7):  # advance to the 8th (last) slide
        nxt.click()

    expect(page.locator(".slide-title")).to_have_text("Live debrief")
    expect(page.locator("#position")).to_have_text("Hotwash · 8 / 8")
    expect(nxt).to_be_disabled()
