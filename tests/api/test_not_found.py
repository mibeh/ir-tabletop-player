"""404 contract: every resource-scoped endpoint returns 404 for unknown IDs.

Pins behavior of `_get_or_404` helpers in both routers. A change that swallows
the 404 (e.g. accidentally returning 500 or 200) gets caught here.
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.asyncio


UNKNOWN = "00000000-0000-4000-8000-000000000000"  # well-formed UUID, no row matches


# ----- Exercises -------------------------------------------------------------

@pytest.mark.parametrize("method,path", [
    ("GET", f"/exercises/{UNKNOWN}"),
    ("DELETE", f"/exercises/{UNKNOWN}"),
    ("POST", f"/exercises/{UNKNOWN}/start"),
    ("POST", f"/exercises/{UNKNOWN}/pause"),
    ("POST", f"/exercises/{UNKNOWN}/resume"),
    ("POST", f"/exercises/{UNKNOWN}/complete"),
    ("POST", f"/exercises/{UNKNOWN}/archive"),
    ("POST", f"/exercises/{UNKNOWN}/unarchive"),
    ("POST", f"/exercises/{UNKNOWN}/present/next"),
    ("POST", f"/exercises/{UNKNOWN}/present/previous"),
])
async def test_exercise_endpoint_returns_404_for_unknown_id(api_client, method, path):
    response = await api_client.request(method, path)
    assert response.status_code == 404, f"{method} {path} -> {response.status_code}: {response.text}"


async def test_exercise_goto_returns_404_for_unknown_id(api_client):
    response = await api_client.post(
        f"/exercises/{UNKNOWN}/present/goto",
        json={"slide_id": "ground_rules"},
    )
    assert response.status_code == 404


async def test_exercise_reveal_returns_404_for_unknown_id(api_client):
    response = await api_client.post(
        f"/exercises/{UNKNOWN}/present/reveal",
        json={"module_idx": 0, "sequence": 1, "question_idx": 0},
    )
    assert response.status_code == 404


async def test_exercise_patch_inject_returns_404_for_unknown_id(api_client):
    response = await api_client.patch(
        f"/exercises/{UNKNOWN}/present/inject",
        json={"module_idx": 0, "sequence": 1, "facilitator_notes": "x"},
    )
    assert response.status_code == 404


async def test_exercise_put_debrief_returns_404_for_unknown_id(api_client):
    response = await api_client.put(
        f"/exercises/{UNKNOWN}/debrief",
        json={"debrief_summary": "x", "follow_up_actions": []},
    )
    assert response.status_code == 404


# ----- Scenarios -------------------------------------------------------------

@pytest.mark.parametrize("method,path", [
    ("GET", f"/scenarios/{UNKNOWN}"),
    ("DELETE", f"/scenarios/{UNKNOWN}"),
    ("GET", f"/scenarios/{UNKNOWN}/download"),
    ("POST", f"/scenarios/{UNKNOWN}/copy"),
])
async def test_scenario_endpoint_returns_404_for_unknown_id(api_client, method, path):
    response = await api_client.request(method, path)
    assert response.status_code == 404, f"{method} {path} -> {response.status_code}: {response.text}"


async def test_scenario_put_returns_404_for_unknown_id(api_client):
    # PUT needs a valid body so validation passes before _get_or_404 runs.
    body = {
        "scenario_id": f"ttx-2026-05-29-{uuid.uuid4().int % 100:02d}",
        "metadata": {"framing": "internal"},
        "exercise_overview": {"name": "x"},
        "scenario_details": {"scenario_type": "ransomware"},
        "modules": [{"injects": [{"sequence": 1}]}],
    }
    response = await api_client.put(f"/scenarios/{UNKNOWN}", json=body)
    assert response.status_code == 404
