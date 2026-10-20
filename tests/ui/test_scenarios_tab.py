"""Scenarios tab — upload, edit-and-save, copy, delete via the UI.

Navigation notes (confirmed against index.html):
- The sidebar nav button text is "Scenarios"; we match it with an anchored
  regex so it doesn't pick up "← Back to scenarios" or row View buttons.
- Per-row actions in the table: only a "View" button.  Copy and Delete live in
  the scenario detail panel that opens when "View" is clicked.
- The scenarios table is rendered inside #panel-scenarios.  Without scoping to
  that panel the locator also matches the hidden dashboard-scenarios table,
  returning invisible elements.
- The detail actions (Copy / Delete) are rendered asynchronously by lit-html,
  so we wait for #scenario-detail-actions button to appear rather than relying
  on networkidle alone.
- copyScenario() stays in the detail panel after copying; we navigate back to
  the Scenarios list to verify the new row.
- deleteScenario() calls showPanel('scenarios') automatically after deletion.
"""
from __future__ import annotations

import json
import re

from playwright.sync_api import expect

from tests.factories import make_scenario_json


def _upload_via_api(page, base_url: str, payload: dict) -> dict:
    """Backstage path: POST the scenario via the API so we can test
    edit/copy/delete without exercising the multi-step upload modal.

    Playwright's multipart FilePayload requires {"name", "mimeType", "buffer"}.
    """
    response = page.request.post(
        f"{base_url}/scenarios",
        multipart={
            "files": {
                "name": "ui-seed.json",
                "mimeType": "application/json",
                "buffer": json.dumps(payload).encode("utf-8"),
            }
        },
    )
    assert response.ok, response.text()
    report = response.json()
    result = report["results"][0]
    assert result["status"] == "created", report
    return {
        "id": result["id"],
        "scenario_id": result["scenario_id"],
        "title": payload["exercise_overview"]["title"],
    }


def _open_scenarios_tab(page, base_url: str) -> None:
    """Navigate to the Scenarios tab via the sidebar button."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    # Sidebar nav button text is "Scenarios" — anchor to avoid ambiguity.
    page.get_by_role("button", name=re.compile(r"^Scenarios$")).click()
    page.wait_for_load_state("networkidle")


def _open_scenario_detail(page, panel, title: str) -> None:
    """Click the View button on the named row and wait for the detail panel.

    Must scope to #panel-scenarios to avoid matching rows in the hidden
    dashboard-scenarios table rendered by the same page.
    """
    row = panel.locator("tbody tr", has_text=title)
    expect(row).to_have_count(1)
    row.locator("button", has_text="View").click()
    # The detail actions (Copy/Delete) are rendered asynchronously by lit-html.
    page.wait_for_selector("#scenario-detail-actions button")


def test_uploaded_scenario_appears_in_scenarios_table(page, base_url):
    payload = make_scenario_json(title="UI Upload Test")
    seeded = _upload_via_api(page, base_url, payload)

    _open_scenarios_tab(page, base_url)
    row = page.locator("#scenarios-table tbody tr", has_text=seeded["title"])
    expect(row).to_have_count(1)


def test_copy_button_creates_copy_suffixed_row(page, base_url):
    payload = make_scenario_json(title="UI Copy Source")
    seeded = _upload_via_api(page, base_url, payload)
    original_title = seeded["title"]

    _open_scenarios_tab(page, base_url)
    panel = page.locator("#panel-scenarios")

    _open_scenario_detail(page, panel, original_title)

    # Click "Copy" in the detail panel actions.
    page.locator("#scenario-detail-actions").locator("button", has_text="Copy").click()
    page.wait_for_load_state("networkidle")

    # copyScenario() stays in the detail panel; navigate back to the list.
    page.get_by_role("button", name=re.compile(r"^Scenarios$")).click()
    page.wait_for_load_state("networkidle")

    copy_title = f"{original_title} (Copy)"
    expect(page.locator("#scenarios-table tbody tr", has_text=copy_title)).to_have_count(1)
    scenarios = page.request.get(f"{base_url}/scenarios").json()["scenarios"]
    copied = next(s for s in scenarios if s["title"] == copy_title)
    assert copied["id"] != seeded["id"]
    assert copied["scenario_id"] != seeded["scenario_id"]


def test_delete_button_removes_row(page, base_url):
    payload = make_scenario_json(title="UI Delete Target")
    seeded = _upload_via_api(page, base_url, payload)
    title = seeded["title"]

    _open_scenarios_tab(page, base_url)
    panel = page.locator("#panel-scenarios")

    _open_scenario_detail(page, panel, title)

    # Click "Delete" in the detail panel actions, then confirm in the modal.
    page.locator("#scenario-detail-actions").locator("button", has_text="Delete").click()
    page.locator("#confirm-modal").get_by_role("button", name="Delete").click()
    page.wait_for_load_state("networkidle")

    # deleteScenario() calls showPanel('scenarios') + loadScenarios(), which
    # re-renders the table via lit-html.  Use expect() for auto-retry so we
    # don't race against the async render.
    expect(page.locator("#panel-scenarios").locator("tr", has_text=title)).to_have_count(0)
