"""Per-file validation errors on POST /scenarios surface in the report, not the status code."""
from __future__ import annotations

import json

import pytest

from tests.factories import make_scenario_json


pytestmark = pytest.mark.asyncio


def _files(payload: dict) -> list:
    return [("files", ("s.json", json.dumps(payload).encode("utf-8"), "application/json"))]


def _only_error(response) -> str:
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["uploaded"] == 0 and body["failed"] == 1, body
    return body["results"][0]["error"]


async def test_bad_scenario_id_regex(api_client):
    payload = make_scenario_json(scenario_id="not-a-valid-id")
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "scenario_id" in error


async def test_invalid_framing(api_client):
    payload = make_scenario_json(framing="not-a-real-framing")
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "framing" in error


async def test_missing_required_top_level_key(api_client):
    payload = make_scenario_json()
    payload.pop("modules")
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "modules" in error.lower()


async def test_empty_modules_array_rejected(api_client):
    payload = make_scenario_json()
    payload["modules"] = []
    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))
    assert "modules" in error.lower()


async def test_non_object_inject_rejected_on_upload(api_client):
    payload = make_scenario_json()
    payload["modules"][0]["injects"][0] = "not an inject object"

    error = _only_error(await api_client.post("/scenarios", files=_files(payload)))

    assert "modules[0].injects[0]" in error


async def test_non_object_inject_rejected_on_update(api_client, seeded_scenario):
    detail = (await api_client.get(f"/scenarios/{seeded_scenario['id']}")).json()
    detail.pop("_audit", None)
    detail["modules"][0]["injects"][0] = "not an inject object"

    response = await api_client.put(
        f"/scenarios/{seeded_scenario['id']}", json=detail
    )

    assert response.status_code == 400
    assert "modules[0].injects[0]" in response.json()["detail"]


async def test_duplicate_scenario_id_reported(api_client, seeded_scenario):
    duplicate = make_scenario_json(scenario_id=seeded_scenario["scenario_id"])
    error = _only_error(await api_client.post("/scenarios", files=_files(duplicate)))
    assert seeded_scenario["scenario_id"] in error


async def test_non_json_upload_reported(api_client):
    files = [("files", ("bad.json", b"not valid json {{", "application/json"))]
    error = _only_error(await api_client.post("/scenarios", files=files))
    assert "JSON" in error
