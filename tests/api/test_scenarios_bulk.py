"""Bulk (multi-file) behavior of POST /scenarios and its per-file report."""
from __future__ import annotations

import pytest

from tests.factories import make_scenario_json, scenario_upload_files

pytestmark = pytest.mark.asyncio


async def test_multi_file_all_success(api_client):
    a = make_scenario_json(scenario_id="ttx-2026-06-02-71")
    b = make_scenario_json(scenario_id="ttx-2026-06-02-72")
    response = await api_client.post("/scenarios", files=scenario_upload_files(a, b))
    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == 2
    assert body["failed"] == 0
    assert [r["status"] for r in body["results"]] == ["created", "created"]
    assert {r["scenario_id"] for r in body["results"]} == {
        "ttx-2026-06-02-71", "ttx-2026-06-02-72",
    }
    # Created entries carry only id + scenario_id (no summary scalars).
    assert set(body["results"][0]) == {"filename", "status", "id", "scenario_id"}


async def test_mixed_batch_partial_success(api_client):
    good = make_scenario_json(scenario_id="ttx-2026-06-02-74")
    bad_json = b"not valid json {{"
    dup = make_scenario_json(scenario_id="ttx-2026-06-02-74")  # same id as good
    response = await api_client.post(
        "/scenarios",
        files=scenario_upload_files(good, bad_json, dup,
                                    filenames=["good.json", "bad.json", "dup.json"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == 1
    assert body["failed"] == 2
    by_name = {r["filename"]: r for r in body["results"]}
    assert by_name["good.json"]["status"] == "created"
    assert by_name["bad.json"]["status"] == "failed"
    assert "JSON" in by_name["bad.json"]["error"]
    assert by_name["dup.json"]["status"] == "failed"
    assert "ttx-2026-06-02-74" in by_name["dup.json"]["error"]
    # Only the good one persisted.
    listing = (await api_client.get("/scenarios")).json()
    ids = [s["scenario_id"] for s in listing["scenarios"]]
    assert ids.count("ttx-2026-06-02-74") == 1


async def test_empty_file_list_is_400(api_client):
    response = await api_client.post("/scenarios")
    assert response.status_code == 400
