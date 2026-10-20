"""Archive, unarchive, delete + list filter for exercises."""
from __future__ import annotations

import pytest

from tests.factories import make_exercise_payload

pytestmark = pytest.mark.asyncio


async def test_archive_stamps_archived_at(api_client, seeded_exercise):
    exercise_id = seeded_exercise["exercise_id"]
    response = await api_client.post(f"/exercises/{exercise_id}/archive")
    assert response.status_code == 200
    body = response.json()
    assert body["archived"] is True
    assert body["archived_at"] is not None


async def test_archive_in_progress_auto_pauses(api_client, running_exercise):
    exercise_id = running_exercise["id"]
    response = await api_client.post(f"/exercises/{exercise_id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "paused"


async def test_list_excludes_archived_by_default(api_client, seeded_exercise, seeded_scenario):
    exercise_id = seeded_exercise["exercise_id"]
    control = await api_client.post(
        "/exercises",
        json=make_exercise_payload(
            scenario_catalog_id=seeded_scenario["id"], title="Visible control exercise",
        ),
    )
    assert control.status_code == 200
    archived = await api_client.post(f"/exercises/{exercise_id}/archive")
    assert archived.status_code == 200

    listing = (await api_client.get("/exercises")).json()
    listed_ids = {e["id"] for e in listing["exercises"]}
    assert control.json()["exercise_id"] in listed_ids
    assert exercise_id not in listed_ids


async def test_list_includes_archived_with_query_flag(api_client, seeded_exercise):
    exercise_id = seeded_exercise["exercise_id"]
    await api_client.post(f"/exercises/{exercise_id}/archive")

    listing = (await api_client.get("/exercises?include_archived=true")).json()
    assert any(e["id"] == exercise_id for e in listing["exercises"])


async def test_unarchive_clears_flag(api_client, seeded_exercise):
    exercise_id = seeded_exercise["exercise_id"]
    await api_client.post(f"/exercises/{exercise_id}/archive")
    response = await api_client.post(f"/exercises/{exercise_id}/unarchive")
    assert response.status_code == 200
    assert response.json() == {"exercise_id": exercise_id, "archived": False}


async def test_delete_then_404(api_client, seeded_exercise):
    exercise_id = seeded_exercise["exercise_id"]
    response = await api_client.delete(f"/exercises/{exercise_id}")
    assert response.status_code == 200
    assert response.json() == {"exercise_id": exercise_id, "deleted": True}
    follow = await api_client.get(f"/exercises/{exercise_id}")
    assert follow.status_code == 404


async def test_delete_in_progress_refused(api_client, running_exercise):
    """A running exercise can't be hard-deleted out from under the facilitator."""
    exercise_id = running_exercise["id"]
    response = await api_client.delete(f"/exercises/{exercise_id}")
    assert response.status_code == 409
    assert "in-progress" in response.json()["detail"].lower()
    # Still present and still in progress.
    follow = await api_client.get(f"/exercises/{exercise_id}")
    assert follow.status_code == 200
    assert follow.json()["status"] == "in_progress"


async def test_delete_allowed_after_pause(api_client, running_exercise):
    """Pausing lifts the in-progress guard so deletion succeeds."""
    exercise_id = running_exercise["id"]
    await api_client.post(f"/exercises/{exercise_id}/pause")
    response = await api_client.delete(f"/exercises/{exercise_id}")
    assert response.status_code == 200
    assert (await api_client.get(f"/exercises/{exercise_id}")).status_code == 404


async def test_archive_is_idempotent(api_client, seeded_exercise):
    """Archiving an already-archived exercise must not bump archived_at."""
    exercise_id = seeded_exercise["exercise_id"]
    first = await api_client.post(f"/exercises/{exercise_id}/archive")
    archived_at_first = first.json()["archived_at"]
    second = await api_client.post(f"/exercises/{exercise_id}/archive")
    assert second.status_code == 200
    assert second.json()["archived_at"] == archived_at_first


async def test_unarchive_on_non_archived_is_noop(api_client, seeded_exercise):
    """Unarchive on an exercise that was never archived returns 200 + archived=False."""
    exercise_id = seeded_exercise["exercise_id"]
    response = await api_client.post(f"/exercises/{exercise_id}/unarchive")
    assert response.status_code == 200
    assert response.json() == {"exercise_id": exercise_id, "archived": False}


async def test_archive_paused_keeps_paused_status(api_client, running_exercise):
    """Auto-pause logic only triggers from in_progress; a paused exercise stays paused."""
    exercise_id = running_exercise["id"]
    await api_client.post(f"/exercises/{exercise_id}/pause")
    response = await api_client.post(f"/exercises/{exercise_id}/archive")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paused"
    assert body["archived"] is True


async def test_archive_debrief_keeps_debrief_status(api_client, debrief_exercise):
    """Archive must not regress status away from debrief."""
    exercise_id = debrief_exercise["id"]
    response = await api_client.post(f"/exercises/{exercise_id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "debrief"
