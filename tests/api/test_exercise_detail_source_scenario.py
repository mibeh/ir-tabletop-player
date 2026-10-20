"""GET /exercises/{id} exposes the source scenario title for the detail view."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_detail_includes_source_scenario_title(api_client, seeded_exercise, seeded_scenario):
    eid = seeded_exercise["exercise_id"]
    detail = (await api_client.get(f"/exercises/{eid}")).json()
    assert detail["scenario_catalog_id"] == seeded_scenario["id"]
    assert detail["source_scenario_title"] == seeded_scenario["title"]


async def test_detail_source_scenario_title_null_when_scenario_deleted(
    api_client, seeded_exercise, seeded_scenario
):
    eid = seeded_exercise["exercise_id"]
    await api_client.delete(f"/scenarios/{seeded_scenario['id']}")
    detail = (await api_client.get(f"/exercises/{eid}")).json()
    # FK is ON DELETE SET NULL, so both the id and the title resolve to null.
    assert detail["scenario_catalog_id"] is None
    assert detail["source_scenario_title"] is None
