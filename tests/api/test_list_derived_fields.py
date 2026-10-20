"""Verify the derived fields exposed by GET /exercises and GET /scenarios.

These fields drive the admin table view; tests pin the response shape so
removing or renaming a field is an obvious breakage.
"""
from __future__ import annotations

import json

import pytest

from tests.factories import expected_deck, make_exercise_payload, make_scenario_json

pytestmark = pytest.mark.asyncio


def _files(payload: dict) -> list:
    return [("files", ("s.json", json.dumps(payload).encode("utf-8"), "application/json"))]


# ----- Scenarios ------------------------------------------------------------

async def test_scenarios_list_includes_inject_count_and_exercise_count(api_client, seeded_scenario):
    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == seeded_scenario["id"])
    # Factory default: 2 modules × 2 injects.
    assert row["inject_count"] == 4
    assert row["exercise_count"] == 0


async def test_scenarios_inject_count_updates_on_put(api_client, seeded_scenario):
    detail = (await api_client.get(f"/scenarios/{seeded_scenario['id']}")).json()
    detail.pop("_audit", None)
    # Strip one inject from the first module — list endpoint must reflect it.
    detail["modules"][0]["injects"] = detail["modules"][0]["injects"][:1]
    put = await api_client.put(f"/scenarios/{seeded_scenario['id']}", json=detail)
    assert put.status_code == 200

    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == seeded_scenario["id"])
    assert row["inject_count"] == 3


async def test_scenarios_exercise_count_reflects_derived_exercises(api_client, seeded_scenario):
    # No exercises yet.
    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == seeded_scenario["id"])
    assert row["exercise_count"] == 0

    # Create two exercises from this scenario.
    await api_client.post("/exercises", json=make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"], title="Run 1"))
    create_two = await api_client.post("/exercises", json=make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"], title="Run 2"))
    second_id = create_two.json()["exercise_id"]

    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == seeded_scenario["id"])
    assert row["exercise_count"] == 2

    # Archiving one must NOT decrement the count (archive is orthogonal).
    await api_client.post(f"/exercises/{second_id}/archive")
    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == seeded_scenario["id"])
    assert row["exercise_count"] == 2


async def test_scenarios_inject_count_for_single_inject_module(api_client):
    """The list summary counts a module's only inject once after upload."""
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-50",
                                  modules=1, injects_per_module=1)
    create = await api_client.post("/scenarios", files=_files(payload))
    assert create.status_code == 200, create.text
    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["scenario_id"] == "ttx-2026-05-29-50")
    assert row["inject_count"] == 1


# ----- Exercises ------------------------------------------------------------

async def test_exercises_list_includes_derived_fields_for_available(api_client, seeded_exercise, seeded_scenario):
    listing = (await api_client.get("/exercises")).json()
    row = next(e for e in listing["exercises"] if e["id"] == seeded_exercise["exercise_id"])
    assert row["source_scenario_title"] == seeded_scenario["title"]
    assert row["participant_count"] == 1
    # Not launched yet: duration + progress fields both null. (slide_total
    # is intentionally null until /start; pre-launch exercises render as "—"
    # rather than "0 / N".)
    assert row["active_duration_minutes"] is None
    assert row["slide_position"] is None
    assert row["slide_total"] is None


async def test_exercises_list_slide_position_advances_after_start_and_next(
    api_client, running_exercise
):
    listing = (await api_client.get("/exercises")).json()
    row = next(e for e in listing["exercises"] if e["id"] == running_exercise["id"])
    deck = expected_deck(running_exercise)
    assert row["slide_total"] == len(deck)
    # /start leaves current_slide at ground_rules → position 1.
    assert row["slide_position"] == 1

    await api_client.post(f"/exercises/{running_exercise['id']}/present/next")
    listing = (await api_client.get("/exercises")).json()
    row = next(e for e in listing["exercises"] if e["id"] == running_exercise["id"])
    assert row["slide_position"] == 2


async def test_exercises_list_source_scenario_title_null_after_catalog_delete(
    api_client, seeded_exercise, seeded_scenario
):
    """Deleting the catalog row leaves the FK null (ON DELETE SET NULL); list
    must surface null rather than 500."""
    delete = await api_client.delete(f"/scenarios/{seeded_scenario['id']}")
    assert delete.status_code == 200

    listing = (await api_client.get("/exercises")).json()
    row = next(e for e in listing["exercises"] if e["id"] == seeded_exercise["exercise_id"])
    assert row["scenario_catalog_id"] is None
    assert row["source_scenario_title"] is None


async def test_exercises_list_slide_position_total_total_for_complete(
    api_client, debrief_exercise
):
    """After hotwash → debrief → complete, list should report position = total.
    current_slide remains at "hotwash" so the presenter can be reopened for
    review; either way deck.index('hotwash') + 1 == total."""
    eid = debrief_exercise["id"]
    await api_client.post(f"/exercises/{eid}/complete")

    listing = (await api_client.get("/exercises")).json()
    row = next(e for e in listing["exercises"] if e["id"] == eid)
    assert row["slide_position"] == row["slide_total"]
    assert row["slide_total"] > 0
