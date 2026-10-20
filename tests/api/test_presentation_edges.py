"""Edge cases in the presentation endpoints.

Complements test_presentation.py which covers the happy paths.
"""
from __future__ import annotations

import asyncio

import pytest

from tests.factories import expected_deck

pytestmark = pytest.mark.asyncio


async def test_debrief_begins_on_arrival_at_hotwash(api_client, running_exercise):
    """Advancing onto the hotwash slide flips status to debrief immediately."""
    eid = running_exercise["id"]
    deck = expected_deck(running_exercise)
    status = None
    for _ in range(len(deck) - 1):
        body = (await api_client.post(f"/exercises/{eid}/present/next")).json()
        status = body["status"]
    assert status == "debrief"
    detail = (await api_client.get(f"/exercises/{eid}")).json()
    assert detail["current_slide"] == "hotwash"
    assert detail["status"] == "debrief"
    assert detail["debrief_started_at"] is not None


async def test_arriving_at_hotwash_while_paused_closes_pause(api_client, running_exercise):
    eid = running_exercise["id"]
    deck = expected_deck(running_exercise)

    pause_response = await api_client.post(f"/exercises/{eid}/pause")
    assert pause_response.status_code == 200
    await asyncio.sleep(1.1)

    for _ in range(len(deck) - 1):
        response = await api_client.post(f"/exercises/{eid}/present/next")
        assert response.status_code == 200, response.text

    detail = (await api_client.get(f"/exercises/{eid}")).json()
    assert detail["status"] == "debrief"
    assert detail["current_slide"] == "hotwash"
    assert detail["paused_at"] is None
    assert detail["paused_total_seconds"] >= 1


async def test_next_on_hotwash_in_debrief_is_noop(api_client, debrief_exercise):
    eid = debrief_exercise["id"]
    resp = await api_client.post(f"/exercises/{eid}/present/next")
    assert resp.status_code == 200
    assert resp.json()["current_slide"] == "hotwash"
    assert resp.json()["status"] == "debrief"


async def test_navigation_allowed_in_debrief(api_client, debrief_exercise):
    """Previous and goto work during debrief so the facilitator can review."""
    eid = debrief_exercise["id"]
    prev = await api_client.post(f"/exercises/{eid}/present/previous")
    assert prev.status_code == 200
    assert prev.json()["current_slide"] != "hotwash"
    goto = await api_client.post(
        f"/exercises/{eid}/present/goto", json={"slide_id": "ground_rules"}
    )
    assert goto.status_code == 200
    assert goto.json()["current_slide"] == "ground_rules"


async def test_reveal_and_patch_rejected_in_debrief(api_client, debrief_exercise):
    """Content mutation is frozen once debrief begins."""
    eid = debrief_exercise["id"]
    reveal = await api_client.post(
        f"/exercises/{eid}/present/reveal",
        json={"module_idx": 0, "sequence": 1, "question_idx": 0},
    )
    assert reveal.status_code == 400
    patch = await api_client.patch(
        f"/exercises/{eid}/present/inject",
        json={"module_idx": 0, "sequence": 1, "facilitator_notes": "x"},
    )
    assert patch.status_code == 400


async def test_reveal_question_idx_out_of_range_is_404(api_client, running_exercise):
    eid = running_exercise["id"]
    response = await api_client.post(
        f"/exercises/{eid}/present/reveal",
        json={"module_idx": 0, "sequence": 1, "question_idx": 999},
    )
    # Handler raises 404 for question out of range (see exercises.py:644).
    assert response.status_code == 404


async def test_reveal_unknown_module_idx_is_404(api_client, running_exercise):
    eid = running_exercise["id"]
    response = await api_client.post(
        f"/exercises/{eid}/present/reveal",
        json={"module_idx": 99, "sequence": 1, "question_idx": 0},
    )
    assert response.status_code == 404


async def test_reveal_unknown_sequence_is_404(api_client, running_exercise):
    eid = running_exercise["id"]
    response = await api_client.post(
        f"/exercises/{eid}/present/reveal",
        json={"module_idx": 0, "sequence": 999, "question_idx": 0},
    )
    assert response.status_code == 404


async def test_patch_inject_expected_actions_out_of_range_is_400(api_client, running_exercise):
    eid = running_exercise["id"]
    response = await api_client.patch(
        f"/exercises/{eid}/present/inject",
        json={"module_idx": 0, "sequence": 1, "expected_actions_checked": [0, 999]},
    )
    assert response.status_code == 400


async def test_patch_inject_dedupes_expected_actions(api_client, running_exercise):
    """Client may send dup indices; server stores each at most once."""
    eid = running_exercise["id"]
    response = await api_client.patch(
        f"/exercises/{eid}/present/inject",
        json={"module_idx": 0, "sequence": 1, "expected_actions_checked": [0, 0, 1, 1, 0]},
    )
    assert response.status_code == 200
    assert response.json()["expected_actions_checked"] == [0, 1]


async def test_patch_inject_unknown_module_idx_is_404(api_client, running_exercise):
    eid = running_exercise["id"]
    response = await api_client.patch(
        f"/exercises/{eid}/present/inject",
        json={"module_idx": 99, "sequence": 1, "facilitator_notes": "x"},
    )
    assert response.status_code == 404


async def test_goto_unknown_slide_id_is_400(api_client, running_exercise):
    eid = running_exercise["id"]
    response = await api_client.post(
        f"/exercises/{eid}/present/goto",
        json={"slide_id": "inject:42:99"},
    )
    assert response.status_code == 400


async def test_goto_to_furthest_slide_itself_is_noop(api_client, running_exercise):
    eid = running_exercise["id"]
    deck = expected_deck(running_exercise)
    # Advance two slides so furthest = deck[2].
    for _ in range(2):
        await api_client.post(f"/exercises/{eid}/present/next")
    response = await api_client.post(
        f"/exercises/{eid}/present/goto",
        json={"slide_id": deck[2]},
    )
    assert response.status_code == 200
    assert response.json()["current_slide"] == deck[2]


async def test_present_endpoints_reject_unlaunched_exercise(api_client, seeded_exercise):
    """Until /start is called, presentation endpoints must reject with 400."""
    eid = seeded_exercise["exercise_id"]
    paths = [
        ("POST", f"/exercises/{eid}/present/next", None),
        ("POST", f"/exercises/{eid}/present/previous", None),
        ("POST", f"/exercises/{eid}/present/goto", {"slide_id": "ground_rules"}),
        ("POST", f"/exercises/{eid}/present/reveal",
         {"module_idx": 0, "sequence": 1, "question_idx": 0}),
        ("PATCH", f"/exercises/{eid}/present/inject",
         {"module_idx": 0, "sequence": 1, "facilitator_notes": "x"}),
    ]
    for method, path, body in paths:
        kwargs = {"json": body} if body is not None else {}
        response = await api_client.request(method, path, **kwargs)
        assert response.status_code == 400, f"{method} {path} -> {response.status_code}"


async def test_present_endpoints_reject_archived_exercise(api_client, running_exercise):
    """Archiving in-progress exercise auto-pauses, but archived bit blocks presentation."""
    eid = running_exercise["id"]
    await api_client.post(f"/exercises/{eid}/archive")
    response = await api_client.post(f"/exercises/{eid}/present/next")
    assert response.status_code == 400
