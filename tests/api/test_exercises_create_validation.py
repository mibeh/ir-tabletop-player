"""POST /exercises input validation.

Pins backend enforcement of the same rules the UI applies in the create form:
- scenario_catalog_id is required and must resolve to an existing scenario
- at least one participant with non-empty name/position/exercise_role/department is required
- exercise_role must be one of Facilitator/Participant/Observer
- title must be non-empty
"""
from __future__ import annotations

import pytest

from tests.factories import make_exercise_payload

pytestmark = pytest.mark.asyncio

UNKNOWN_SCENARIO = "00000000-0000-4000-8000-000000000000"


async def test_missing_scenario_catalog_id_is_422(api_client):
    payload = make_exercise_payload()
    payload.pop("scenario_catalog_id", None)
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 422


async def test_empty_scenario_catalog_id_is_422(api_client):
    payload = make_exercise_payload(scenario_catalog_id="")
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 422


async def test_unknown_scenario_catalog_id_is_404(api_client):
    payload = make_exercise_payload(scenario_catalog_id=UNKNOWN_SCENARIO)
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 404


async def test_empty_participants_is_422(api_client, seeded_scenario):
    payload = make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"],
        participants=[],
    )
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 422


async def test_valid_new_shape_participant_is_accepted_and_stored(api_client, seeded_scenario):
    participant = {
        "name": "Jane Doe",
        "position": "CISO",
        "exercise_role": "Facilitator",
        "department": "Security",
    }
    payload = make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"],
        participants=[participant],
    )
    create = await api_client.post("/exercises", json=payload)
    assert create.status_code == 200, create.text
    detail = await api_client.get(f"/exercises/{create.json()['exercise_id']}")
    assert detail.json()["participants"][0] == participant


@pytest.mark.parametrize("bad_field", ["name", "position", "exercise_role", "department"])
async def test_participant_with_empty_field_is_422(api_client, seeded_scenario, bad_field):
    participant = {
        "name": "n",
        "position": "Analyst",
        "exercise_role": "Participant",
        "department": "Security",
    }
    participant[bad_field] = ""
    payload = make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"],
        participants=[participant],
    )
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 422


async def test_participant_with_invalid_exercise_role_is_422(api_client, seeded_scenario):
    participant = {
        "name": "n",
        "position": "Analyst",
        "exercise_role": "Captain",
        "department": "Security",
    }
    payload = make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"],
        participants=[participant],
    )
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 422


async def test_empty_title_is_422(api_client, seeded_scenario):
    payload = make_exercise_payload(
        scenario_catalog_id=seeded_scenario["id"],
        title="",
    )
    response = await api_client.post("/exercises", json=payload)
    assert response.status_code == 422


