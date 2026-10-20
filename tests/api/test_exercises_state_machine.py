"""Exhaustive state-machine rejection coverage.

For each action, walks an exercise into every status that should reject it
and asserts 400. Catches accidental loosening of the lifecycle guards in
api/routes/exercises.py.
"""
from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.asyncio


async def _pause(api_client, eid):
    return await api_client.post(f"/exercises/{eid}/pause")


async def _resume(api_client, eid):
    return await api_client.post(f"/exercises/{eid}/resume")


async def _start(api_client, eid):
    return await api_client.post(f"/exercises/{eid}/start")


async def _complete(api_client, eid):
    return await api_client.post(f"/exercises/{eid}/complete")


# ----- pause from non-in_progress ------------------------------------------

async def test_pause_rejected_from_available(api_client, seeded_exercise):
    response = await _pause(api_client, seeded_exercise["exercise_id"])
    assert response.status_code == 400


async def test_pause_rejected_from_paused(api_client, running_exercise):
    eid = running_exercise["id"]
    await _pause(api_client, eid)
    response = await _pause(api_client, eid)
    assert response.status_code == 400


async def test_pause_rejected_from_debrief(api_client, debrief_exercise):
    response = await _pause(api_client, debrief_exercise["id"])
    assert response.status_code == 400


async def test_pause_rejected_from_complete(api_client, debrief_exercise):
    eid = debrief_exercise["id"]
    await _complete(api_client, eid)
    response = await _pause(api_client, eid)
    assert response.status_code == 400


# ----- resume from non-paused -----------------------------------------------

async def test_resume_rejected_from_available(api_client, seeded_exercise):
    response = await _resume(api_client, seeded_exercise["exercise_id"])
    assert response.status_code == 400


async def test_resume_rejected_from_in_progress(api_client, running_exercise):
    response = await _resume(api_client, running_exercise["id"])
    assert response.status_code == 400


async def test_resume_rejected_from_debrief(api_client, debrief_exercise):
    response = await _resume(api_client, debrief_exercise["id"])
    assert response.status_code == 400


async def test_resume_rejected_from_complete(api_client, debrief_exercise):
    eid = debrief_exercise["id"]
    await _complete(api_client, eid)
    response = await _resume(api_client, eid)
    assert response.status_code == 400


# ----- start from non-available ---------------------------------------------

async def test_start_rejected_from_in_progress(api_client, running_exercise):
    response = await _start(api_client, running_exercise["id"])
    assert response.status_code == 400


async def test_start_rejected_from_paused(api_client, running_exercise):
    eid = running_exercise["id"]
    await _pause(api_client, eid)
    response = await _start(api_client, eid)
    assert response.status_code == 400


async def test_start_rejected_from_debrief(api_client, debrief_exercise):
    response = await _start(api_client, debrief_exercise["id"])
    assert response.status_code == 400


async def test_start_rejected_from_complete(api_client, debrief_exercise):
    eid = debrief_exercise["id"]
    await _complete(api_client, eid)
    response = await _start(api_client, eid)
    assert response.status_code == 400


# ----- complete from non-debrief --------------------------------------------

async def test_complete_rejected_from_available(api_client, seeded_exercise):
    response = await _complete(api_client, seeded_exercise["exercise_id"])
    assert response.status_code == 400


async def test_complete_rejected_from_in_progress(api_client, running_exercise):
    response = await _complete(api_client, running_exercise["id"])
    assert response.status_code == 400


async def test_complete_rejected_from_paused(api_client, running_exercise):
    eid = running_exercise["id"]
    await _pause(api_client, eid)
    response = await _complete(api_client, eid)
    assert response.status_code == 400


async def test_complete_rejected_from_complete(api_client, debrief_exercise):
    eid = debrief_exercise["id"]
    await _complete(api_client, eid)
    response = await _complete(api_client, eid)
    assert response.status_code == 400


# ----- multi-cycle pause/resume accumulation --------------------------------

async def test_multiple_pause_resume_cycles_accumulate(api_client, running_exercise):
    """Two pause/resume cycles should sum paused_total_seconds, not overwrite."""
    eid = running_exercise["id"]

    await _pause(api_client, eid)
    await asyncio.sleep(1.1)
    first = (await _resume(api_client, eid)).json()
    first_total = first["paused_total_seconds"]
    assert first_total >= 1

    await _pause(api_client, eid)
    await asyncio.sleep(1.1)
    second = (await _resume(api_client, eid)).json()
    second_total = second["paused_total_seconds"]

    assert second_total >= first_total + 1, (
        f"second total {second_total} should add to first {first_total}"
    )
