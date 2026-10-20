"""Create-exercise form collects the four participant fields and the roster shows them.

Navigation notes (confirmed against index.html):
- "+ New Exercise" button (in #panel-exercises) calls showPanel('create-exercise').
- The create form lives in #panel-create-exercise: #ex-title, #ex-scenario-catalog
  (a <select> of scenario templates), and #participants-container holding
  .participant-row rows with .p-name / .p-position / .p-exercise-role / .p-department.
- On success createExercise() shows a success alert then calls
  loadExerciseDetail() after ~1.5s, landing on #panel-exercise-detail where
  #participants-table renders the roster.
"""
from __future__ import annotations

import json
import re

from playwright.sync_api import expect

from tests.factories import make_scenario_json


def _seed_scenario(page, base_url: str) -> dict:
    resp = page.request.post(
        f"{base_url}/scenarios",
        multipart={
            "files": {
                "name": "s.json",
                "mimeType": "application/json",
                "buffer": json.dumps(make_scenario_json(title="Create-Form Scenario")).encode("utf-8"),
            }
        },
    )
    assert resp.ok, resp.text()
    return resp.json()["results"][0]


def test_create_form_collects_four_fields_and_roster_shows_them(page, base_url):
    scenario = _seed_scenario(page, base_url)

    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    # Navigate to the Exercises panel first (the "New Exercise" button lives there).
    page.get_by_role("button", name=re.compile(r"^Exercises$")).click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile(r"New Exercise")).first.click()

    page.fill("#ex-title", "Participant Fields UI Test")
    page.select_option("#ex-scenario-catalog", scenario["id"])

    row = page.locator(".participant-row").first
    row.locator(".p-name").fill("Jane Doe")
    row.locator(".p-position").fill("CISO")
    row.locator(".p-exercise-role").select_option("Facilitator")
    row.locator(".p-department").fill("Security")

    page.get_by_role("button", name=re.compile(r"Create Exercise")).click()

    # createExercise() redirects to the detail view, which renders the roster.
    page.wait_for_selector("#participants-table table", timeout=5000)
    table = page.locator("#participants-table")
    expect(table.get_by_text("Jane Doe")).to_have_count(1)
    expect(table.get_by_text("CISO")).to_have_count(1)
    expect(table.get_by_text("Facilitator")).to_have_count(1)
    expect(table.get_by_text("Security")).to_have_count(1)
    # Column headers reflect the new fields, not the old Role/Email.
    expect(table.get_by_role("columnheader", name=re.compile(r"Position"))).to_have_count(1)
    expect(table.get_by_role("columnheader", name=re.compile(r"Exercise Role"))).to_have_count(1)
    expect(table.get_by_role("columnheader", name=re.compile(r"Department"))).to_have_count(1)
