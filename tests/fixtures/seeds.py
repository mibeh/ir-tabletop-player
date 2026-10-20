"""Stateful seed fixtures that create rows via the real API."""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest_asyncio

from tests.factories import expected_deck, make_exercise_payload, make_scenario_json


@pytest_asyncio.fixture
async def seeded_scenario(api_client) -> Dict[str, Any]:
    """Upload one scenario via POST /scenarios. Returns its list summary row."""
    payload = make_scenario_json()
    files = [("files", ("seeded.json", json.dumps(payload).encode("utf-8"), "application/json"))]
    response = await api_client.post("/scenarios", files=files)
    assert response.status_code == 200, response.text
    created = response.json()["results"][0]
    assert created["status"] == "created", response.text
    listing = (await api_client.get("/scenarios")).json()
    return next(s for s in listing["scenarios"] if s["id"] == created["id"])


@pytest_asyncio.fixture
async def seeded_exercise(api_client, seeded_scenario) -> Dict[str, Any]:
    """Create an exercise from `seeded_scenario`. Status: available."""
    payload = make_exercise_payload(scenario_catalog_id=seeded_scenario["id"])
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


@pytest_asyncio.fixture
async def running_exercise(api_client, seeded_exercise) -> Dict[str, Any]:
    """seeded_exercise + /start. Status: in_progress, current_slide=ground_rules."""
    exercise_id = seeded_exercise["exercise_id"]
    response = await api_client.post(f"/exercises/{exercise_id}/start")
    assert response.status_code == 200, response.text
    detail = await api_client.get(f"/exercises/{exercise_id}")
    return detail.json()


@pytest_asyncio.fixture
async def debrief_exercise(api_client, running_exercise) -> Dict[str, Any]:
    """running_exercise advanced through every slide until status=debrief."""
    exercise_id = running_exercise["id"]
    deck = expected_deck(running_exercise)
    # One /present/next per deck slide moves through every position; one more
    # advances past hotwash into debrief. +2 absorbs off-by-one mistakes.
    max_steps = len(deck) + 2
    for _ in range(max_steps):
        response = await api_client.post(f"/exercises/{exercise_id}/present/next")
        assert response.status_code == 200, response.text
        if response.json().get("status") == "debrief":
            break
    else:
        raise AssertionError(
            f"did not reach debrief within {max_steps} /present/next calls "
            f"(deck length={len(deck)})"
        )
    detail = await api_client.get(f"/exercises/{exercise_id}")
    return detail.json()
