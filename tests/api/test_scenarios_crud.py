"""POST/GET/PUT/DELETE + download for the scenarios catalog."""
from __future__ import annotations

import json

import pytest

from tests.factories import make_scenario_json


pytestmark = pytest.mark.asyncio


def _files(payload: dict) -> list:
    return [("files", ("s.json", json.dumps(payload).encode("utf-8"), "application/json"))]


async def test_post_reports_created_and_persists_scalars(api_client):
    payload = make_scenario_json()
    response = await api_client.post("/scenarios", files=_files(payload))
    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == 1
    assert body["failed"] == 0
    created = body["results"][0]
    assert set(created) == {"filename", "status", "id", "scenario_id"}
    assert created["status"] == "created"
    assert created["scenario_id"] == payload["scenario_id"]
    assert "id" in created
    # Denormalized scalars are verified via the list summary row.
    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == created["id"])
    assert row["title"] == payload["exercise_overview"]["name"]
    assert row["scenario_type"] == "ransomware"
    assert row["framing"] == "internal"
    assert row["difficulty"] == "intermediate"
    assert row["module_count"] == 2


async def test_list_returns_uploaded_scenario(api_client, seeded_scenario):
    response = await api_client.get("/scenarios")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert any(s["id"] == seeded_scenario["id"] for s in body["scenarios"])


async def test_get_detail_reconstitutes_full_ctep(api_client, seeded_scenario):
    response = await api_client.get(f"/scenarios/{seeded_scenario['id']}")
    assert response.status_code == 200
    body = response.json()
    # All nine top-level CTEP keys present.
    for key in (
        "scenario_id", "metadata", "exercise_overview", "participant_roles",
        "exercise_guidelines", "scenario_details", "modules", "hotwash",
        "appendices", "success_criteria",
    ):
        assert key in body, f"missing CTEP key: {key}"
    # Plus the _audit envelope.
    assert body["_audit"]["id"] == seeded_scenario["id"]


async def test_put_updates_modules_and_recomputes_module_count(api_client, seeded_scenario):
    # Fetch, mutate, PUT back.
    detail = (await api_client.get(f"/scenarios/{seeded_scenario['id']}")).json()
    detail["modules"].append({
        "order": 99,
        "title": "Extra Module",
        "injects": [{"sequence": 1, "title": "Extra", "narrative": "n",
                     "discussion_questions": [], "expected_actions": []}],
    })
    detail.pop("_audit", None)  # caller drops the envelope; handler also strips defensively
    response = await api_client.put(f"/scenarios/{seeded_scenario['id']}", json=detail)
    assert response.status_code == 200
    # Re-fetch as summary via list to confirm module_count scalar was recomputed.
    listing = (await api_client.get("/scenarios")).json()
    row = next(s for s in listing["scenarios"] if s["id"] == seeded_scenario["id"])
    assert row["module_count"] == 3


async def test_download_returns_attachment_with_round_trippable_json(api_client, seeded_scenario):
    response = await api_client.get(f"/scenarios/{seeded_scenario['id']}/download")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    disp = response.headers["content-disposition"]
    assert "attachment" in disp
    assert seeded_scenario["scenario_id"] in disp
    body = json.loads(response.text)
    assert body["scenario_id"] == seeded_scenario["scenario_id"]


async def test_delete_then_404(api_client, seeded_scenario):
    rid = seeded_scenario["id"]
    response = await api_client.delete(f"/scenarios/{rid}")
    assert response.status_code == 200
    assert response.json() == {"id": rid, "deleted": True}
    follow = await api_client.get(f"/scenarios/{rid}")
    assert follow.status_code == 404
