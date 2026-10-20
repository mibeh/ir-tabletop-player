"""Exercises tab — list, detail, Begin Exercise.

Navigation notes (confirmed against index.html):
- The sidebar nav button text is "🎯 All Exercises" (with emoji), so we match
  with a regex locator.
- Exercises table is rendered inside #exercises-table inside #panel-exercises.
  Scope to that panel to avoid matching rows in the hidden recent-exercises
  table on the dashboard.
- Row action is a "View →" button — the exercise title is not directly
  clickable as a link.
- Exercise detail renders in #panel-exercise-detail with actions in
  #detail-actions rendered asynchronously by lit-html.
- The "▶ Begin Exercise" button has an emoji prefix; match with regex.
- launchPresentation() calls window.open() for two popup windows BEFORE
  POSTing /start, so we suppress popups via page.context "popup" handler.
- POST /exercises expects a JSON body; use json= kwarg via page.request or
  manually set Content-Type.
- The POST /exercises response contains exercise_id (string UUID). The
  GET /exercises/{id} response uses "id" for the same value.
"""
from __future__ import annotations

import json
import re
from uuid import uuid4

from playwright.sync_api import expect

from tests.factories import make_exercise_payload, make_scenario_json


def _seed_exercise_via_api(page, base_url: str) -> tuple[dict, dict]:
    """Create a scenario then an exercise seeded from it. Returns (scenario, exercise)."""
    suffix = uuid4().hex[:8]
    scenario_payload = make_scenario_json(title=f"Exercise-Tab Scenario {suffix}")
    scenario_resp = page.request.post(
        f"{base_url}/scenarios",
        multipart={
            "files": {
                "name": "s.json",
                "mimeType": "application/json",
                "buffer": json.dumps(scenario_payload).encode("utf-8"),
            }
        },
    )
    assert scenario_resp.ok, scenario_resp.text()
    scenario = scenario_resp.json()["results"][0]

    exercise_payload = make_exercise_payload(
        scenario_catalog_id=scenario["id"],
        title=f"UI Exercise Smoke {suffix}",
    )
    exercise_resp = page.request.post(
        f"{base_url}/exercises",
        data=json.dumps(exercise_payload),
        headers={"content-type": "application/json"},
    )
    assert exercise_resp.ok, exercise_resp.text()
    exercise = exercise_resp.json()
    return scenario, exercise


def _open_exercises_tab(page, base_url: str) -> None:
    """Navigate to the Exercises tab via the sidebar button."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile(r"^Exercises$")).click()
    page.wait_for_load_state("networkidle")


def test_exercise_appears_in_exercises_table(page, base_url):
    _, exercise = _seed_exercise_via_api(page, base_url)

    _open_exercises_tab(page, base_url)
    panel = page.locator("#panel-exercises")
    expect(panel.locator("#exercises-table").get_by_text(exercise["title"], exact=True)).to_have_count(1)


def test_clicking_exercise_row_opens_detail(page, base_url):
    _, exercise = _seed_exercise_via_api(page, base_url)

    _open_exercises_tab(page, base_url)
    panel = page.locator("#panel-exercises")

    # Click "View →" on the matching row.
    row = panel.locator("tbody tr", has_text=exercise["title"])
    expect(row).to_have_count(1)
    row.locator("button", has_text="View").click()

    # Wait for the detail panel actions to be rendered by lit-html.
    page.wait_for_selector("#detail-actions button")

    expect(page.locator("#detail-title")).to_have_text(exercise["title"])
    expect(page.locator("#detail-content").get_by_text(re.compile(r"Module 1"))).not_to_have_count(0)


def test_launch_presentation_calls_start(page, base_url):
    _, exercise = _seed_exercise_via_api(page, base_url)
    exercise_id = exercise["exercise_id"]

    # Suppress popup windows opened by launchPresentation() before the /start call.
    page.context.on("popup", lambda p: p.close())

    # Deep-link directly to the exercise detail via hash routing.
    page.goto(f"{base_url}/#exercise={exercise_id}")
    page.wait_for_load_state("networkidle")

    # Wait for the detail actions panel (lit-html async render).
    page.wait_for_selector("#detail-actions button")

    with page.expect_response(
        lambda r: r.request.method == "POST" and r.url.endswith(f"/exercises/{exercise_id}/start")
    ) as start_response:
        page.get_by_role("button", name=re.compile(r"Begin Exercise")).click()
    assert start_response.value.status == 200
    detail = page.request.get(f"{base_url}/exercises/{exercise_id}").json()
    assert detail["status"] == "in_progress"
