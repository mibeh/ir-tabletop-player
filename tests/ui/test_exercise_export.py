"""UI: Download Package button on completed exercises.

The live server runs in a subprocess that shares its parent shell's cwd, so
files land in `./exercise_reports/` relative to wherever pytest is invoked.
The test cleans up the file returned by the export endpoint.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import expect

from tests.factories import make_exercise_payload, make_scenario_json


def _seed_scenario(page, base_url: str, title: str) -> dict:
    payload = make_scenario_json(title=title)
    r = page.request.post(
        f"{base_url}/scenarios",
        multipart={"files": {
            "name": "s.json",
            "mimeType": "application/json",
            "buffer": json.dumps(payload).encode("utf-8"),
        }},
    )
    assert r.ok, r.text()
    return r.json()["results"][0]


def _seed_available_exercise(page, base_url: str) -> dict:
    scenario = _seed_scenario(page, base_url, "Export UI Available Source")
    body = make_exercise_payload(
        scenario_catalog_id=scenario["id"],
        title="Export UI Available",
    )
    r = page.request.post(
        f"{base_url}/exercises",
        data=json.dumps(body),
        headers={"content-type": "application/json"},
    )
    assert r.ok, r.text()
    return r.json()


def _seed_complete_exercise(page, base_url: str) -> dict:
    scenario = _seed_scenario(page, base_url, "Export UI Complete Source")
    body = make_exercise_payload(
        scenario_catalog_id=scenario["id"],
        title="Export UI Complete",
    )
    created = page.request.post(
        f"{base_url}/exercises",
        data=json.dumps(body),
        headers={"content-type": "application/json"},
    )
    assert created.ok, created.text()
    ex = created.json()
    eid = ex["exercise_id"]
    assert page.request.post(f"{base_url}/exercises/{eid}/start").ok
    for _ in range(200):
        r = page.request.post(f"{base_url}/exercises/{eid}/present/next")
        assert r.ok, r.text()
        if r.json().get("status") == "debrief":
            break
    else:
        raise AssertionError("exercise did not reach debrief")
    assert page.request.post(f"{base_url}/exercises/{eid}/complete").ok
    return ex


def test_download_button_hidden_when_not_complete(page, base_url):
    ex = _seed_available_exercise(page, base_url)
    page.goto(f"{base_url}/#exercise={ex['exercise_id']}")
    page.wait_for_selector("#detail-actions button")
    expect(
        page.locator("#detail-actions").get_by_role(
            "button", name=re.compile(r"Download Package")
        )
    ).to_have_count(0)


def test_download_button_writes_file_for_complete_exercise(page, base_url):
    ex = _seed_complete_exercise(page, base_url)

    page.goto(f"{base_url}/#exercise={ex['exercise_id']}")
    page.wait_for_selector("#detail-actions button")
    with page.expect_response(
        lambda r: r.request.method == "POST" and r.url.endswith(
            f"/exercises/{ex['exercise_id']}/export"
        )
    ) as export_response:
        page.locator("#detail-actions").get_by_role(
            "button", name=re.compile(r"Download Package")
        ).click()

    assert export_response.value.status == 200
    written = Path(export_response.value.json()["path"])
    try:
        assert written.exists()
        payload = json.loads(written.read_text())
        assert payload["package_version"] == 1
        assert payload["exercise"]["id"] == ex["exercise_id"]
        assert payload["exercise"]["status"] == "complete"
    finally:
        written.unlink(missing_ok=True)
