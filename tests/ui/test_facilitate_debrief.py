"""UI: the hotwash slide is the facilitator's debrief workspace.

Reaching hotwash enters debrief; the facilitator view stays on the slide
(no redirect), shows a Complete Exercise control, and completing returns to
the admin detail view.
"""
from __future__ import annotations

import json
import re

from playwright.sync_api import expect

from tests.ui._helpers import advance_to, seed_exercise


def test_facilitator_stays_on_hotwash_in_debrief(page, base_url):
    eid = seed_exercise(page, base_url, title="Debrief Scenario")
    advance_to(page, base_url, eid, "hotwash")
    page.goto(f"{base_url}/facilitate.html#{eid}")
    # Status is debrief, but the view stays on the hotwash slide.
    expect(page.get_by_role("button", name="Complete Exercise")).to_be_visible()
    # The hotwash slide content stays rendered (its heading), proving the view
    # did not redirect away when status became debrief.
    expect(page.get_by_text("Live debrief")).to_be_visible()


def test_complete_exercise_from_hotwash_returns_to_admin(page, base_url):
    eid = seed_exercise(page, base_url, title="Debrief Scenario")
    advance_to(page, base_url, eid, "hotwash")
    page.goto(f"{base_url}/facilitate.html#{eid}")
    page.get_by_role("button", name="Complete Exercise").click()
    expect(page).to_have_url(re.compile(r"#exercise="))
    detail = page.request.get(f"{base_url}/exercises/{eid}").json()
    assert detail["status"] == "complete"


def test_debrief_summary_editable_on_hotwash(page, base_url):
    eid = seed_exercise(page, base_url, title="Debrief Scenario")
    advance_to(page, base_url, eid, "hotwash")
    page.goto(f"{base_url}/facilitate.html#{eid}")

    with page.expect_response(
        lambda r: r.request.method == "PUT"
        and r.url.endswith(f"/exercises/{eid}/debrief")
        and json.loads(r.request.post_data or "{}").get("debrief_summary")
        == "Key gaps identified."
    ) as save_response:
        page.get_by_placeholder(re.compile("Debrief summary")).fill("Key gaps identified.")
    assert save_response.value.status == 200

    detail = page.request.get(f"{base_url}/exercises/{eid}").json()
    assert detail["debrief_summary"] == "Key gaps identified."


def test_debrief_followup_action_editable_on_hotwash(page, base_url):
    eid = seed_exercise(page, base_url, title="Debrief Scenario")
    advance_to(page, base_url, eid, "hotwash")
    page.goto(f"{base_url}/facilitate.html#{eid}")

    with page.expect_response(
        lambda r: r.request.method == "PUT"
        and r.url.endswith(f"/exercises/{eid}/debrief")
        and {"owner": "SecOps", "action": "Rotate keys"}
        in json.loads(r.request.post_data or "{}").get("follow_up_actions", [])
    ) as save_response:
        page.get_by_role("button", name=re.compile("Add action")).click()
        page.get_by_placeholder("Owner").fill("SecOps")
        page.get_by_placeholder("Action item").fill("Rotate keys")
    assert save_response.value.status == 200

    detail = page.request.get(f"{base_url}/exercises/{eid}").json()
    assert any(
        a.get("owner") == "SecOps" and a.get("action") == "Rotate keys"
        for a in detail["follow_up_actions"]
    )
