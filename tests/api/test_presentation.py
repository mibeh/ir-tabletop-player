"""Presentation controls: /present/next, /previous, /goto, /reveal, PATCH inject.

Deck layout is computed dynamically from the seeded scenario's modules; see
``tests.factories.expected_deck`` which mirrors ``_compute_deck`` in
``api/routes/exercises.py``.
"""
from __future__ import annotations

import pytest

from tests.factories import expected_deck

pytestmark = pytest.mark.asyncio


async def test_present_next_walks_deck_and_advances_furthest(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    deck = expected_deck(running_exercise)
    response = await api_client.post(f"/exercises/{exercise_id}/present/next")
    assert response.status_code == 200
    body = response.json()
    assert body["current_slide"] == deck[1]
    assert body["furthest_slide"] == deck[1]


async def test_present_next_stamps_released_at_on_inject_slide(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    deck = expected_deck(running_exercise)
    first_inject_slide = next(s for s in deck if s.startswith("inject:"))
    first_inject_idx = deck.index(first_inject_slide)
    # Walk forward until we land on the first inject slide.
    for _ in range(first_inject_idx):
        await api_client.post(f"/exercises/{exercise_id}/present/next")
    body = (await api_client.get(f"/exercises/{exercise_id}")).json()
    assert body["current_slide"] == first_inject_slide

    _, m_idx, seq = first_inject_slide.split(":")
    inject = next(
        i for i in body["modules"][int(m_idx)]["injects"]
        if i["sequence"] == int(seq)
    )
    assert inject.get("released_at") is not None


async def test_present_previous_does_not_regress_furthest(api_client, running_exercise):
    """Regression test for fc76406: backward nav must not move furthest_slide back."""
    exercise_id = running_exercise["id"]
    deck = expected_deck(running_exercise)
    # Advance to a mid-deck slide (4th position if the deck is long enough).
    target_idx = min(4, len(deck) - 2)  # never land on hotwash itself
    for _ in range(target_idx):
        await api_client.post(f"/exercises/{exercise_id}/present/next")
    after_forward = (await api_client.get(f"/exercises/{exercise_id}")).json()
    furthest_after_forward = after_forward["furthest_slide"]
    assert furthest_after_forward == deck[target_idx]

    # Walk back twice → current regresses, furthest must NOT.
    await api_client.post(f"/exercises/{exercise_id}/present/previous")
    await api_client.post(f"/exercises/{exercise_id}/present/previous")
    after_back = (await api_client.get(f"/exercises/{exercise_id}")).json()
    assert after_back["furthest_slide"] == furthest_after_forward
    assert after_back["current_slide"] != furthest_after_forward

    # Advance one → still must not regress furthest below previous max.
    await api_client.post(f"/exercises/{exercise_id}/present/next")
    after_forward_again = (await api_client.get(f"/exercises/{exercise_id}")).json()
    assert after_forward_again["furthest_slide"] == furthest_after_forward


async def test_present_previous_at_ground_rules_is_noop(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    response = await api_client.post(f"/exercises/{exercise_id}/present/previous")
    assert response.status_code == 200
    assert response.json()["current_slide"] == "ground_rules"


async def test_present_goto_to_visited_slide_succeeds(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    deck = expected_deck(running_exercise)
    # Advance to deck[2] (first inject if 2-module scenario), then jump back to deck[1].
    for _ in range(2):
        await api_client.post(f"/exercises/{exercise_id}/present/next")
    response = await api_client.post(
        f"/exercises/{exercise_id}/present/goto",
        json={"slide_id": deck[1]},
    )
    assert response.status_code == 200
    assert response.json()["current_slide"] == deck[1]


async def test_present_goto_forward_jump_rejected(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    deck = expected_deck(running_exercise)
    # Current = ground_rules, furthest = ground_rules. Jump to a later slide.
    response = await api_client.post(
        f"/exercises/{exercise_id}/present/goto",
        json={"slide_id": deck[2]},
    )
    assert response.status_code == 400


async def test_present_reveal_adds_question_idx(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    response = await api_client.post(
        f"/exercises/{exercise_id}/present/reveal",
        json={"module_idx": 0, "sequence": 1, "question_idx": 0},
    )
    assert response.status_code == 200
    assert response.json()["revealed_questions"] == [0]

    # Idempotent — revealing the same question again doesn't double up.
    response = await api_client.post(
        f"/exercises/{exercise_id}/present/reveal",
        json={"module_idx": 0, "sequence": 1, "question_idx": 0},
    )
    assert response.json()["revealed_questions"] == [0]


async def test_patch_inject_saves_facilitator_notes(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    response = await api_client.patch(
        f"/exercises/{exercise_id}/present/inject",
        json={"module_idx": 0, "sequence": 1, "facilitator_notes": "Saw this in 2025."},
    )
    assert response.status_code == 200
    assert response.json()["facilitator_notes"] == "Saw this in 2025."


async def test_patch_inject_checks_expected_actions(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    response = await api_client.patch(
        f"/exercises/{exercise_id}/present/inject",
        json={"module_idx": 0, "sequence": 1, "expected_actions_checked": [0, 1]},
    )
    assert response.status_code == 200
    assert response.json()["expected_actions_checked"] == [0, 1]
