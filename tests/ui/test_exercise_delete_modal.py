"""UI: per-exercise delete confirmation modal on the detail view.

The detail view exposes a Delete button that opens a confirmation modal
(not a browser confirm). Confirming hard-deletes the exercise via
DELETE /exercises/{id} and returns to the list; cancelling leaves it intact.
"""
from __future__ import annotations

import json

from playwright.sync_api import expect

from tests.factories import make_exercise_payload, make_scenario_json


def _seed_exercise(page, base_url: str, title: str) -> str:
    scenario = page.request.post(
        f"{base_url}/scenarios",
        multipart={"files": {
            "name": "s.json",
            "mimeType": "application/json",
            "buffer": json.dumps(make_scenario_json(title=f"{title} Source")).encode("utf-8"),
        }},
    ).json()["results"][0]
    ex = page.request.post(
        f"{base_url}/exercises",
        data=json.dumps(make_exercise_payload(
            scenario_catalog_id=scenario["id"],
            title=title,
        )),
        headers={"content-type": "application/json"},
    ).json()
    return ex["exercise_id"]


def test_delete_modal_opens_with_exercise_name(page, base_url):
    eid = _seed_exercise(page, base_url, "Delete Modal Target")
    page.goto(f"{base_url}/#exercise={eid}")
    page.wait_for_selector("#detail-actions button")

    expect(page.locator("#confirm-modal")).not_to_be_visible()
    page.locator("#detail-actions").get_by_role("button", name="Delete").click()

    expect(page.locator("#confirm-modal")).to_be_visible()
    expect(page.locator("#confirm-modal-message")).to_contain_text("Delete Modal Target")


def test_cancel_leaves_exercise_intact(page, base_url):
    eid = _seed_exercise(page, base_url, "Keep Me")
    page.goto(f"{base_url}/#exercise={eid}")
    page.wait_for_selector("#detail-actions button")

    page.locator("#detail-actions").get_by_role("button", name="Delete").click()
    page.locator("#confirm-modal").get_by_role("button", name="Cancel").click()

    expect(page.locator("#confirm-modal")).not_to_be_visible()
    assert page.request.get(f"{base_url}/exercises/{eid}").ok


def test_escape_cancels_modal(page, base_url):
    eid = _seed_exercise(page, base_url, "Escape Me")
    page.goto(f"{base_url}/#exercise={eid}")
    page.wait_for_selector("#detail-actions button")

    page.locator("#detail-actions").get_by_role("button", name="Delete").click()
    expect(page.locator("#confirm-modal")).to_be_visible()
    page.keyboard.press("Escape")

    expect(page.locator("#confirm-modal")).not_to_be_visible()
    assert page.request.get(f"{base_url}/exercises/{eid}").ok


def test_delete_disabled_while_in_progress(page, base_url):
    eid = _seed_exercise(page, base_url, "Running Exercise")
    assert page.request.post(f"{base_url}/exercises/{eid}/start").ok
    page.goto(f"{base_url}/#exercise={eid}")
    page.wait_for_selector("#detail-actions button")

    delete_btn = page.locator("#detail-actions").get_by_role("button", name="Delete")
    expect(delete_btn).to_be_disabled()


def test_confirm_deletes_and_returns_to_list(page, base_url):
    eid = _seed_exercise(page, base_url, "Delete Me For Real")
    page.goto(f"{base_url}/#exercise={eid}")
    page.wait_for_selector("#detail-actions button")

    page.locator("#detail-actions").get_by_role("button", name="Delete").click()
    page.locator("#confirm-modal").get_by_role(
        "button", name="Delete Exercise"
    ).click()

    expect(page.locator("#panel-exercises")).to_be_visible()
    assert page.request.get(f"{base_url}/exercises/{eid}").status == 404
