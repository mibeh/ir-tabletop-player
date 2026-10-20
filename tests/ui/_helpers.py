"""Shared Playwright helpers for UI tests.

Seeds scenarios/exercises through the real API so UI test files don't
duplicate setup. Mirrors the import style of tests.factories.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from tests.factories import make_exercise_payload, make_scenario_json


def seed_exercise(
    page,
    base_url: str,
    *,
    title: str = "UI Scenario",
    appendices: Optional[Dict[str, Any]] = None,
    start: bool = True,
) -> str:
    """Create a scenario + exercise via the API; optionally /start it.

    Returns the exercise id. With ``start=False`` the exercise stays in
    ``available`` status (for views that show the pre-launch state).
    """
    scenario_kwargs: Dict[str, Any] = {"title": title}
    if appendices is not None:
        scenario_kwargs["appendices"] = appendices
    scenario = page.request.post(
        f"{base_url}/scenarios",
        multipart={"files": {
            "name": "s.json",
            "mimeType": "application/json",
            "buffer": json.dumps(make_scenario_json(**scenario_kwargs)).encode("utf-8"),
        }},
    ).json()["results"][0]
    ex = page.request.post(
        f"{base_url}/exercises",
        data=json.dumps(make_exercise_payload(
            scenario_catalog_id=scenario["id"], title=f"{title} Run",
        )),
        headers={"content-type": "application/json"},
    ).json()
    eid = ex["exercise_id"]
    if start:
        page.request.post(f"{base_url}/exercises/{eid}/start")
    return eid


def advance_to(page, base_url: str, eid: str, slide_id: str) -> None:
    """POST /present/next until the exercise's current_slide is slide_id."""
    for _ in range(50):
        r = page.request.post(f"{base_url}/exercises/{eid}/present/next").json()
        if r.get("current_slide") == slide_id:
            return
    raise AssertionError(f"never reached {slide_id}")
