"""Exercise state machine: available → in_progress ⇄ paused → debrief → complete."""
from __future__ import annotations

import asyncio

import pytest

from tests.factories import make_exercise_payload


pytestmark = pytest.mark.asyncio


async def test_create_from_scenario_copies_ctep_fields(api_client, seeded_scenario):
    payload = make_exercise_payload(scenario_catalog_id=seeded_scenario["id"])
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert "exercise_id" in body

    detail = (await api_client.get(f"/exercises/{body['exercise_id']}")).json()
    assert detail["status"] == "available"
    assert detail["scenario_catalog_id"] == seeded_scenario["id"]
    assert len(detail["modules"]) == 2  # copied from seeded scenario
    assert detail["participants"] == payload["participants"]
    # scenario_type is derived from the scenario row, not the request body.
    assert detail["scenario_type"] == seeded_scenario["scenario_type"]


async def test_start_transitions_to_in_progress(api_client, seeded_exercise):
    exercise_id = seeded_exercise["exercise_id"]
    response = await api_client.post(f"/exercises/{exercise_id}/start")
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    detail = (await api_client.get(f"/exercises/{exercise_id}")).json()
    assert detail["status"] == "in_progress"
    assert detail["started_at"] is not None
    assert detail["current_slide"] == "ground_rules"
    assert detail["furthest_slide"] == "ground_rules"


async def test_pause_then_resume_accumulates_paused_seconds(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    pause = await api_client.post(f"/exercises/{exercise_id}/pause")
    assert pause.status_code == 200
    assert pause.json()["status"] == "paused"

    await asyncio.sleep(1.1)  # ensure at least 1s elapses

    resume = await api_client.post(f"/exercises/{exercise_id}/resume")
    assert resume.status_code == 200
    body = resume.json()
    assert body["status"] == "in_progress"
    assert body["paused_total_seconds"] >= 1


async def test_walk_deck_releases_every_inject(api_client, debrief_exercise):
    # debrief_exercise fixture already walked the deck; verify every inject got
    # a released_at stamp and final status is debrief.
    assert debrief_exercise["status"] == "debrief"
    for module in debrief_exercise["modules"]:
        for inject in module["injects"]:
            assert inject.get("released_at"), \
                f"inject {module['order']}.{inject['sequence']} missing released_at"


async def test_put_debrief_persists_summary_and_followups(api_client, debrief_exercise):
    exercise_id = debrief_exercise["id"]
    body = {
        "debrief_summary": "Smoke test debrief.",
        "follow_up_actions": [{"description": "Fix X", "owner": "team"}],
    }
    response = await api_client.put(f"/exercises/{exercise_id}/debrief", json=body)
    assert response.status_code == 200

    detail = (await api_client.get(f"/exercises/{exercise_id}")).json()
    assert detail["debrief_summary"] == "Smoke test debrief."
    assert detail["follow_up_actions"] == [{"description": "Fix X", "owner": "team"}]


async def test_complete_from_debrief(api_client, debrief_exercise):
    response = await api_client.post(f"/exercises/{debrief_exercise['id']}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "complete"


async def test_completed_at_stamped_on_complete(api_client, debrief_exercise):
    exercise_id = debrief_exercise["id"]
    await api_client.post(f"/exercises/{exercise_id}/complete")
    detail = (await api_client.get(f"/exercises/{exercise_id}")).json()
    assert detail["status"] == "complete"
    assert detail["completed_at"] is not None


async def test_get_exercise_returns_all_expected_keys(api_client, debrief_exercise):
    """Pin the response shape so the shared _exercise_to_dict serializer
    can't quietly drop or add keys when also used by /export."""
    await api_client.post(f"/exercises/{debrief_exercise['id']}/complete")
    resp = await api_client.get(f"/exercises/{debrief_exercise['id']}")
    assert resp.status_code == 200
    expected_keys = {
        "id", "title", "scenario_type", "status", "scenario_catalog_id",
        "source_scenario_title", "current_slide", "furthest_slide", "exercise_overview",
        "exercise_guidelines", "modules", "success_criteria", "hotwash",
        "appendices", "participants", "created_at", "started_at",
        "debrief_started_at", "paused_at", "paused_total_seconds",
        "completed_at", "archived", "archived_at", "debrief_summary",
        "follow_up_actions", "metrics",
    }
    assert set(resp.json().keys()) == expected_keys
