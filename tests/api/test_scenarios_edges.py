"""Edge cases in scenarios CRUD that the main CRUD/validation tests don't cover.

- PUT scenario_id collision
- PUT scenario_id renamed to a fresh unique value
- POST framing=None vs framing missing (both accepted)
- POST metadata as non-object rejected
"""
from __future__ import annotations

import json

import pytest

from tests.factories import make_scenario_json

pytestmark = pytest.mark.asyncio


def _files(payload: dict) -> list:
    return [("files", ("s.json", json.dumps(payload).encode("utf-8"), "application/json"))]


def _created_id(response) -> str:
    assert response.status_code == 200, response.text
    created = response.json()["results"][0]
    assert created["status"] == "created", response.text
    return created["id"]


def _only_error(response) -> str:
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["failed"] == 1, body
    return body["results"][0]["error"]


async def test_put_scenario_id_collision_returns_409(api_client):
    """Renaming a scenario to another row's scenario_id must conflict."""
    first = make_scenario_json(scenario_id="ttx-2026-05-29-90")
    second = make_scenario_json(scenario_id="ttx-2026-05-29-91")
    first_id = _created_id(await api_client.post("/scenarios", files=_files(first)))
    second_id = _created_id(await api_client.post("/scenarios", files=_files(second)))

    detail = (await api_client.get(f"/scenarios/{second_id}")).json()
    detail.pop("_audit", None)
    detail["scenario_id"] = "ttx-2026-05-29-90"  # collide with `first`
    response = await api_client.put(f"/scenarios/{second_id}", json=detail)
    assert response.status_code == 409
    # Cleanup so other tests aren't affected.
    await api_client.delete(f"/scenarios/{first_id}")
    await api_client.delete(f"/scenarios/{second_id}")


async def test_put_scenario_id_rename_to_fresh_id_succeeds(api_client, seeded_scenario):
    """Renaming to a unique scenario_id is allowed."""
    detail = (await api_client.get(f"/scenarios/{seeded_scenario['id']}")).json()
    detail.pop("_audit", None)
    new_id = "ttx-2026-05-29-77"
    detail["scenario_id"] = new_id
    response = await api_client.put(f"/scenarios/{seeded_scenario['id']}", json=detail)
    assert response.status_code == 200
    assert response.json()["scenario_id"] == new_id


async def test_post_framing_none_is_accepted(api_client):
    """metadata.framing=None is treated as missing, per scenarios.py:55."""
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-80")
    payload["metadata"]["framing"] = None
    response = await api_client.post("/scenarios", files=_files(payload))
    assert response.json()["results"][0]["status"] == "created"


async def test_post_framing_missing_is_accepted(api_client):
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-81")
    payload["metadata"].pop("framing", None)
    response = await api_client.post("/scenarios", files=_files(payload))
    assert response.json()["results"][0]["status"] == "created"


async def test_post_metadata_as_string_is_reported(api_client):
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-82")
    payload["metadata"] = "not-an-object"
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "metadata" in error


async def test_post_scenario_details_as_string_is_reported(api_client):
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-83")
    payload["scenario_details"] = "not-an-object"
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "scenario_details" in error


async def test_post_exercise_overview_as_string_is_reported(api_client):
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-84")
    payload["exercise_overview"] = "not-an-object"
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "exercise_overview" in error


async def test_post_modules_with_empty_injects_is_reported(api_client):
    payload = make_scenario_json(scenario_id="ttx-2026-05-29-85")
    payload["modules"][0]["injects"] = []
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "injects" in error


async def test_put_strips_audit_envelope(api_client, seeded_scenario):
    """Defensive: PUT body containing _audit must not blow up validation."""
    detail = (await api_client.get(f"/scenarios/{seeded_scenario['id']}")).json()
    # Leave _audit in the body — handler strips it (scenarios.py:266).
    response = await api_client.put(f"/scenarios/{seeded_scenario['id']}", json=detail)
    assert response.status_code == 200
