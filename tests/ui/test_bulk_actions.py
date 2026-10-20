"""Bulk-action UI: select multiple rows → bulk bar → Archive/Delete."""
from __future__ import annotations

import json
import re
from uuid import uuid4

from playwright.sync_api import expect

from tests.factories import make_exercise_payload, make_scenario_json


def _seed_n_scenarios(page, base_url, n):
    out = []
    batch = uuid4().hex[:8]
    for i in range(n):
        title = f"Bulk Scenario {batch} {i}"
        payload = make_scenario_json(title=title)
        resp = page.request.post(
            f"{base_url}/scenarios",
            multipart={
                "files": {
                    "name": "s.json",
                    "mimeType": "application/json",
                    "buffer": json.dumps(payload).encode("utf-8"),
                }
            },
        )
        assert resp.ok, resp.text()
        created = resp.json()["results"][0]
        out.append({"title": title, "id": created["id"], "scenario_id": created["scenario_id"]})
    return out


def _seed_n_exercises(page, base_url, n):
    batch = uuid4().hex[:8]
    scenario_payload = make_scenario_json(title=f"Bulk Source {batch}")
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

    out = []
    for i in range(n):
        body = make_exercise_payload(
            scenario_catalog_id=scenario["id"],
            title=f"Bulk Exercise {batch} {i}",
        )
        resp = page.request.post(
            f"{base_url}/exercises",
            data=json.dumps(body),
            headers={"content-type": "application/json"},
        )
        assert resp.ok, resp.text()
        out.append(resp.json())
    return out


def _open_exercises_tab(page, base_url: str) -> None:
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile(r"^Exercises$")).click()
    page.wait_for_load_state("networkidle")


def _open_scenarios_tab(page, base_url: str) -> None:
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile(r"^Scenarios$")).click()
    page.wait_for_load_state("networkidle")


def _check_exercise_row(page, title: str) -> None:
    """Check the selection checkbox on an exercise row by title."""
    panel = page.locator("#exercises-table")
    row = panel.locator("tbody tr", has_text=title)
    expect(row).to_have_count(1)
    row.locator('input[type="checkbox"]').check()


def _check_scenario_row(page, title: str) -> None:
    """Check the selection checkbox on a scenario row by title."""
    panel = page.locator("#scenarios-table")
    row = panel.locator("tbody tr", has_text=title)
    expect(row).to_have_count(1)
    row.locator('input[type="checkbox"]').check()


def _exercises_bulk_bar(page):
    """Return a locator for the bulk bar inside #exercises-table."""
    # The bulk bar is rendered inside #exercises-table as the first child div.
    # It contains a <strong> with the count followed by text " selected".
    return page.locator("#exercises-table div", has=page.locator("strong")).first


def _scenarios_bulk_bar(page):
    """Return a locator for the bulk bar inside #scenarios-table."""
    return page.locator("#scenarios-table div", has=page.locator("strong")).first


def _confirm_modal(page, name: str) -> None:
    """Click the accept button in the shared confirmation modal."""
    page.locator("#confirm-modal").get_by_role("button", name=name).click()


def test_bulk_bar_appears_when_exercise_rows_checked(page, base_url):
    exercises = _seed_n_exercises(page, base_url, 2)

    _open_exercises_tab(page, base_url)

    for ex in exercises:
        _check_exercise_row(page, ex["title"])

    # The bulk bar <strong> should show "2".
    bulk_bar = _exercises_bulk_bar(page)
    expect(bulk_bar).to_be_visible()
    expect(bulk_bar.locator("strong")).to_have_text("2")


def test_bulk_archive_exercises_removes_from_default_list(page, base_url):
    exercises = _seed_n_exercises(page, base_url, 2)
    ex_ids = [ex["exercise_id"] for ex in exercises]

    _open_exercises_tab(page, base_url)

    for ex in exercises:
        _check_exercise_row(page, ex["title"])

    # Wait for lit-html to re-render the bulk bar (count must show 2).
    expect(_exercises_bulk_bar(page).locator("strong")).to_have_text("2")

    page.locator("#exercises-table").get_by_role("button", name="Archive").click()
    _confirm_modal(page, "Archive")
    for ex in exercises:
        expect(page.locator("#exercises-table tbody tr", has_text=ex["title"])).to_have_count(0)

    # Verify via the API: the exercises should now be archived.
    for ex_id in ex_ids:
        resp = page.request.get(f"{base_url}/exercises/{ex_id}")
        assert resp.ok
        assert resp.json()["archived"] is True


def test_bulk_delete_exercises_returns_404_on_direct_get(page, base_url):
    exercises = _seed_n_exercises(page, base_url, 2)

    _open_exercises_tab(page, base_url)

    for ex in exercises:
        _check_exercise_row(page, ex["title"])

    # Wait for bulk bar to confirm both are selected.
    expect(_exercises_bulk_bar(page).locator("strong")).to_have_text("2")

    page.locator("#exercises-table").get_by_role("button", name="Delete").click()
    _confirm_modal(page, "Delete")
    for ex in exercises:
        expect(page.locator("#exercises-table tbody tr", has_text=ex["title"])).to_have_count(0)

    for ex in exercises:
        response = page.request.get(f"{base_url}/exercises/{ex['exercise_id']}")
        assert response.status == 404


def test_bulk_delete_scenarios_returns_404_on_direct_get(page, base_url):
    scenarios = _seed_n_scenarios(page, base_url, 2)

    _open_scenarios_tab(page, base_url)

    for s in scenarios:
        _check_scenario_row(page, s["title"])

    # Wait for bulk bar to confirm both are selected.
    expect(_scenarios_bulk_bar(page).locator("strong")).to_have_text("2")

    page.locator("#scenarios-table").get_by_role("button", name="Delete").click()
    _confirm_modal(page, "Delete")
    for scenario in scenarios:
        expect(page.locator("#scenarios-table tbody tr", has_text=scenario["title"])).to_have_count(0)

    for s in scenarios:
        response = page.request.get(f"{base_url}/scenarios/{s['id']}")
        assert response.status == 404
