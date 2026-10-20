"""POST /scenarios/{id}/copy — ID minting + Copy suffix."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_copy_mints_new_scenario_id_and_appends_copy_suffix(api_client, seeded_scenario):
    response = await api_client.post(f"/scenarios/{seeded_scenario['id']}/copy")
    assert response.status_code == 200
    copy = response.json()
    assert copy["id"] != seeded_scenario["id"]
    assert copy["scenario_id"] != seeded_scenario["scenario_id"]
    # Minted scenario_id uses today's UTC date prefix.
    assert copy["scenario_id"].startswith("ttx-")
    # Title gets " (Copy)" suffix via exercise_overview.name.
    detail = (await api_client.get(f"/scenarios/{copy['id']}")).json()
    assert detail["exercise_overview"]["name"].endswith(" (Copy)")


async def test_copy_of_copy_increments_suffix(api_client, seeded_scenario):
    first = (await api_client.post(f"/scenarios/{seeded_scenario['id']}/copy")).json()
    second = (await api_client.post(f"/scenarios/{first['id']}/copy")).json()
    assert first["scenario_id"] != second["scenario_id"]
    # Both share the date prefix; the numeric NN suffix differs.
    f_prefix, f_n = first["scenario_id"].rsplit("-", 1)
    s_prefix, s_n = second["scenario_id"].rsplit("-", 1)
    assert f_prefix == s_prefix
    assert int(s_n) > int(f_n)
