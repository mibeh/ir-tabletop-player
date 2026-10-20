"""Producer/consumer contract tests across endpoint boundaries.

The original create-exercise bug shipped because the scenarios catalog
accepted a `scenario_type` value that the create-exercise endpoint then
rejected. Wherever one endpoint writes state another endpoint reads, the
two can drift. These tests pin each pair.

The scenario_type cases exercise the full catalog-to-completion path here.
"""
from __future__ import annotations

import copy
import json

import pytest

from tests.factories import (
    expected_deck,
    make_exercise_payload,
    make_module,
    make_scenario_json,
)


# Realistic scenario_type values observed in production scenarios. The first
# two are NOT in the legacy ScenarioType enum and caused the original bug.
REAL_SCENARIO_TYPES = [
    "business_email_compromise",
    "zero_day_exploit-vendor_responsibility",
    "ransomware",
    "supply_chain",
]


async def _upload_scenario(api_client, payload):
    files = [("files", ("s.json", json.dumps(payload).encode("utf-8"), "application/json"))]
    r = await api_client.post("/scenarios", files=files)
    assert r.status_code == 200, r.text
    created = r.json()["results"][0]
    assert created["status"] == "created", r.text
    return created


async def _create_and_walk(api_client, scenario_id):
    """Create an exercise from a catalog scenario, drive to debrief+complete.

    Returns the final detail dict. Any failure surfaces a contract mismatch
    between the catalog data shape and the exercise consumer.
    """
    payload = make_exercise_payload(scenario_catalog_id=scenario_id)
    r = await api_client.post("/exercises", json=payload)
    assert r.status_code == 200, f"create rejected catalog scenario: {r.text}"
    exercise_id = r.json()["exercise_id"]

    r = await api_client.post(f"/exercises/{exercise_id}/start")
    assert r.status_code == 200, r.text

    detail = (await api_client.get(f"/exercises/{exercise_id}")).json()
    deck = expected_deck({"modules": detail["modules"]})
    for _ in range(len(deck) + 2):
        r = await api_client.post(f"/exercises/{exercise_id}/present/next")
        assert r.status_code == 200, r.text
        if r.json().get("status") == "debrief":
            break
    else:
        raise AssertionError(
            f"could not reach debrief from scenario {scenario_id} "
            f"(deck length={len(deck)})"
        )

    r = await api_client.post(f"/exercises/{exercise_id}/complete")
    assert r.status_code == 200, r.text
    return (await api_client.get(f"/exercises/{exercise_id}")).json()


# ---------------------------------------------------------------------------
# A. Catalog producer → exercise consumer
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario_type", REAL_SCENARIO_TYPES)
async def test_uploaded_scenario_runs_full_exercise_lifecycle(api_client, scenario_type):
    """Strongest catalog→exercise contract: any uploaded scenario must
    support the entire lifecycle (create → start → walk every slide →
    debrief → complete). Catches type drift AND modules/inject shape drift."""
    scenario = await _upload_scenario(
        api_client, make_scenario_json(scenario_type=scenario_type),
    )
    catalog_detail = (await api_client.get(f"/scenarios/{scenario['id']}")).json()
    assert catalog_detail["scenario_details"]["scenario_type"] == scenario_type
    detail = await _create_and_walk(api_client, scenario["id"])
    assert detail["status"] == "complete"
    assert detail["scenario_type"] == scenario_type


@pytest.mark.parametrize("modules,injects_per_module", [
    (1, 1),    # minimal — one module, one inject
    (1, 5),    # one module, many injects
    (5, 2),    # many modules, two injects each
    (3, 3),    # mid-size
])
async def test_uploaded_scenario_with_varying_shapes_runs_lifecycle(
    api_client, modules, injects_per_module,
):
    """The exercise consumer must accept every module/inject shape the
    catalog producer accepts. Varies deck size to surface off-by-one bugs
    in the deck walker that wouldn't show up with the default 2x2."""
    scenario = await _upload_scenario(
        api_client,
        make_scenario_json(modules=modules, injects_per_module=injects_per_module),
    )
    detail = await _create_and_walk(api_client, scenario["id"])
    assert detail["status"] == "complete"


async def test_put_edited_scenario_remains_exerciseable(api_client, seeded_scenario):
    """PUT /scenarios/{id} must not produce a row that POST /exercises rejects."""
    detail = (await api_client.get(f"/scenarios/{seeded_scenario['id']}")).json()
    edited = copy.deepcopy(detail)
    edited["scenario_details"]["scenario_type"] = "business_email_compromise"
    edited["modules"].append(make_module(order=99, inject_count=1))
    r = await api_client.put(f"/scenarios/{seeded_scenario['id']}", json=edited)
    assert r.status_code == 200, r.text

    final = await _create_and_walk(api_client, seeded_scenario["id"])
    assert final["status"] == "complete"
    assert final["scenario_type"] == "business_email_compromise"


async def test_copied_scenario_remains_exerciseable(api_client, seeded_scenario):
    """POST /scenarios/{id}/copy must produce a row that POST /exercises accepts."""
    r = await api_client.post(f"/scenarios/{seeded_scenario['id']}/copy")
    assert r.status_code == 200, r.text
    copy_id = r.json()["id"]

    detail = await _create_and_walk(api_client, copy_id)
    assert detail["status"] == "complete"


# ---------------------------------------------------------------------------
# B. Runtime mutators → GET /exercises/{id} (detail) roundtrip
# ---------------------------------------------------------------------------

async def test_patch_inject_runtime_fields_visible_in_detail(api_client, running_exercise):
    """PATCH /present/inject writes inject runtime fields; GET detail must
    surface them. A future _exercise_to_dict refactor that drops the fields
    breaks the facilitator UI silently — the existing test_patch tests only
    assert the PATCH response."""
    eid = running_exercise["id"]
    r = await api_client.patch(
        f"/exercises/{eid}/present/inject",
        json={
            "module_idx": 0,
            "sequence": 1,
            "expected_actions_checked": [0, 1],
            "facilitator_notes": "Roundtrip note.",
        },
    )
    assert r.status_code == 200, r.text

    detail = (await api_client.get(f"/exercises/{eid}")).json()
    inj = next(
        i for i in detail["modules"][0]["injects"] if i["sequence"] == 1
    )
    assert inj.get("expected_actions_checked") == [0, 1]
    assert inj.get("facilitator_notes") == "Roundtrip note."


async def test_reveal_question_visible_in_detail(api_client, running_exercise):
    """POST /present/reveal appends to revealed_questions; GET detail must
    echo it. Drift would break the presenter view's reveal indicator."""
    eid = running_exercise["id"]
    r = await api_client.post(
        f"/exercises/{eid}/present/reveal",
        json={"module_idx": 0, "sequence": 1, "question_idx": 0},
    )
    assert r.status_code == 200, r.text

    detail = (await api_client.get(f"/exercises/{eid}")).json()
    inj = next(
        i for i in detail["modules"][0]["injects"] if i["sequence"] == 1
    )
    assert inj.get("revealed_questions") == [0]


async def test_archive_state_visible_in_detail_and_list(
    api_client, running_exercise,
):
    """POST /archive sets archived=True; both detail AND list must reflect
    it. The list omits archived rows by default — the include_archived
    branch must echo the same shape."""
    eid = running_exercise["id"]
    r = await api_client.post(f"/exercises/{eid}/archive")
    assert r.status_code == 200, r.text

    detail = (await api_client.get(f"/exercises/{eid}")).json()
    assert detail["archived"] is True
    assert detail["archived_at"] is not None

    # Default list excludes archived rows.
    default = (await api_client.get("/exercises")).json()
    assert all(e["id"] != eid for e in default["exercises"])

    # With include_archived, the archived row appears and carries the flag.
    inclusive = (await api_client.get("/exercises?include_archived=true")).json()
    row = next(e for e in inclusive["exercises"] if e["id"] == eid)
    assert row["archived"] is True


# ---------------------------------------------------------------------------
# C. List-response shape contracts (consumer: admin UI tables)
# ---------------------------------------------------------------------------

# Keys the UI's scenarios table and create-exercise dropdown read off each
# row. Verified against api/static/index.html (renderScenariosTable and
# loadScenarioCatalogOptions). If a key is added/renamed/removed, the UI
# breaks; this test forces both sides to stay aligned.
SCENARIO_LIST_KEYS_REQUIRED = {
    "id", "scenario_id", "title", "scenario_type", "framing", "difficulty",
    "module_count", "inject_count", "exercise_count", "created_at",
}


async def test_scenarios_list_row_shape(api_client, seeded_scenario):
    r = await api_client.get("/scenarios")
    assert r.status_code == 200, r.text
    rows = r.json()["scenarios"]
    assert rows, "expected at least one scenario row"
    missing = SCENARIO_LIST_KEYS_REQUIRED - set(rows[0].keys())
    assert not missing, f"scenarios list row missing UI-required keys: {missing}"


# Keys the UI's exercises table reads (renderExercisesTable). The detail
# shape is pinned separately by test_get_exercise_returns_all_expected_keys.
EXERCISE_LIST_KEYS_REQUIRED = {
    "id", "title", "status", "scenario_catalog_id", "source_scenario_title",
    "participant_count", "active_duration_minutes", "slide_position",
    "slide_total", "created_at", "started_at", "completed_at", "archived",
    "archived_at",
}


async def test_exercises_list_row_shape(api_client, seeded_exercise):
    r = await api_client.get("/exercises")
    assert r.status_code == 200, r.text
    rows = r.json()["exercises"]
    assert rows, "expected at least one exercise row"
    missing = EXERCISE_LIST_KEYS_REQUIRED - set(rows[0].keys())
    assert not missing, f"exercises list row missing UI-required keys: {missing}"
