"""Tests for POST /exercises/{id}/export (Completion Package)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from api.routes.exercises import _slugify_title
from tests.factories import expected_deck, make_exercise_payload


# -- Slug helper ------------------------------------------------------------

def test_slugify_basic():
    assert _slugify_title("Q2 Ransomware Tabletop") == "q2-ransomware-tabletop"


def test_slugify_collapses_runs_of_punct():
    assert _slugify_title("Foo   ---  Bar!!") == "foo-bar"


def test_slugify_strips_path_traversal():
    # Critical: the slug must never contain / or . that could break out of
    # the output directory.
    assert "/" not in _slugify_title("../../etc/passwd")
    assert "." not in _slugify_title("../../etc/passwd")
    assert ".." not in _slugify_title("../../etc/passwd")


def test_slugify_truncates_to_60_chars():
    long = "a" * 200
    assert len(_slugify_title(long)) == 60


def test_slugify_empty_when_no_alphanumeric():
    assert _slugify_title("   ") == ""
    assert _slugify_title("!!!") == ""


# -- Endpoint --------------------------------------------------------------

@pytest.fixture
def cwd_tmp(monkeypatch, tmp_path):
    """Redirect ./exercise_reports/ to a per-test tmp dir."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


async def _create_exercise(api_client, scenario_id, title="Export Target"):
    payload = make_exercise_payload(scenario_catalog_id=scenario_id, title=title)
    r = await api_client.post("/exercises", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["exercise_id"]


async def _drive_to_debrief(api_client, exercise_id):
    """Start the exercise, walk every slide, land in debrief."""
    r = await api_client.post(f"/exercises/{exercise_id}/start")
    assert r.status_code == 200
    detail = (await api_client.get(f"/exercises/{exercise_id}")).json()
    deck = expected_deck({"modules": detail["modules"]})
    for _ in range(len(deck) + 2):
        r = await api_client.post(f"/exercises/{exercise_id}/present/next")
        assert r.status_code == 200, r.text
        if r.json().get("status") == "debrief":
            return
    raise AssertionError("did not reach debrief")


async def _drive_to_complete(api_client, exercise_id):
    await _drive_to_debrief(api_client, exercise_id)
    r = await api_client.post(f"/exercises/{exercise_id}/complete")
    assert r.status_code == 200


async def test_export_writes_file_and_returns_path(
    api_client, debrief_exercise, cwd_tmp,
):
    exercise_id = debrief_exercise["id"]
    await api_client.post(f"/exercises/{exercise_id}/complete")

    r = await api_client.post(f"/exercises/{exercise_id}/export")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["filename"].startswith("exercise-")
    assert body["filename"].endswith(".json")
    assert body["path"] == f"exercise_reports/{body['filename']}"
    assert body["bytes_written"] > 0

    written = cwd_tmp / body["path"]
    assert written.exists()
    payload = json.loads(written.read_text())

    assert payload["package_version"] == 1
    assert "exported_at" in payload
    ex = payload["exercise"]
    assert ex["id"] == exercise_id
    assert ex["status"] == "complete"
    assert "metrics" in ex
    assert "modules" in ex
    assert "completed_at" in ex


async def test_export_rejects_available(api_client, seeded_exercise, cwd_tmp):
    r = await api_client.post(f"/exercises/{seeded_exercise['exercise_id']}/export")
    assert r.status_code == 400
    assert "completed" in r.json()["detail"].lower()
    assert not (cwd_tmp / "exercise_reports").exists()


async def test_export_rejects_in_progress(api_client, running_exercise, cwd_tmp):
    r = await api_client.post(f"/exercises/{running_exercise['id']}/export")
    assert r.status_code == 400
    assert not (cwd_tmp / "exercise_reports").exists()


async def test_export_rejects_paused(api_client, running_exercise, cwd_tmp):
    eid = running_exercise["id"]
    await api_client.post(f"/exercises/{eid}/pause")
    r = await api_client.post(f"/exercises/{eid}/export")
    assert r.status_code == 400
    assert not (cwd_tmp / "exercise_reports").exists()


async def test_export_rejects_debrief(api_client, debrief_exercise, cwd_tmp):
    r = await api_client.post(f"/exercises/{debrief_exercise['id']}/export")
    assert r.status_code == 400
    assert not (cwd_tmp / "exercise_reports").exists()


async def test_export_unknown_id_returns_404(api_client, cwd_tmp):
    r = await api_client.post("/exercises/does-not-exist/export")
    assert r.status_code == 404


async def test_export_works_when_archived(api_client, debrief_exercise, cwd_tmp):
    eid = debrief_exercise["id"]
    await api_client.post(f"/exercises/{eid}/complete")
    await api_client.post(f"/exercises/{eid}/archive")
    r = await api_client.post(f"/exercises/{eid}/export")
    assert r.status_code == 200


async def test_export_filename_resists_path_traversal(
    api_client, seeded_scenario, cwd_tmp,
):
    """Title with traversal characters must produce a slug that stays in-dir."""
    eid = await _create_exercise(
        api_client, seeded_scenario["id"], title="../../etc/passwd",
    )
    await _drive_to_complete(api_client, eid)

    r = await api_client.post(f"/exercises/{eid}/export")
    assert r.status_code == 200
    body = r.json()
    assert ".." not in body["filename"]
    assert "/" not in body["filename"]

    written = (cwd_tmp / body["path"]).resolve()
    reports_dir = (cwd_tmp / "exercise_reports").resolve()
    assert str(written).startswith(str(reports_dir) + "/")


async def test_export_repeated_calls_produce_distinct_files(
    api_client, debrief_exercise, cwd_tmp, monkeypatch,
):
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    monkeypatch.setattr("api.routes.exercises.datetime", FrozenDatetime)
    eid = debrief_exercise["id"]
    await api_client.post(f"/exercises/{eid}/complete")

    r1 = await api_client.post(f"/exercises/{eid}/export")
    assert r1.status_code == 200
    r2 = await api_client.post(f"/exercises/{eid}/export")
    assert r2.status_code == 200

    assert r1.json()["filename"] != r2.json()["filename"]
    for response in (r1, r2):
        payload = json.loads((cwd_tmp / response.json()["path"]).read_text())
        assert payload["exercise"]["id"] == eid


async def test_export_preserves_existing_file_on_name_collision(
    api_client, debrief_exercise, cwd_tmp, monkeypatch,
):
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    monkeypatch.setattr("api.routes.exercises.datetime", FrozenDatetime)
    eid = debrief_exercise["id"]
    await api_client.post(f"/exercises/{eid}/complete")
    reports = cwd_tmp / "exercise_reports"
    reports.mkdir()
    existing = reports / "exercise-smoke-test-exercise-20260101-120000.json"
    existing.write_text("existing package", encoding="utf-8")

    response = await api_client.post(f"/exercises/{eid}/export")

    assert response.status_code == 200
    assert response.json()["filename"] == "exercise-smoke-test-exercise-20260101-120000-2.json"
    assert existing.read_text(encoding="utf-8") == "existing package"
    exported = json.loads((cwd_tmp / response.json()["path"]).read_text())
    assert exported["exercise"]["id"] == eid
