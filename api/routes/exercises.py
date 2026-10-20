"""Exercise lifecycle endpoints."""
from __future__ import annotations

import copy
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.exercise import Exercise, ExerciseStatus
from src.models.scenario import Scenario

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exercises", tags=["exercises"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ParticipantInput(BaseModel):
    name: str = Field(min_length=1)
    position: str = Field(min_length=1)
    exercise_role: Literal["Facilitator", "Participant", "Observer"]
    department: str = Field(min_length=1)


class CreateExerciseRequest(BaseModel):
    title: str = Field(min_length=1)
    participants: List[ParticipantInput] = Field(min_length=1)
    scenario_catalog_id: str = Field(min_length=1)


class DebriefRequest(BaseModel):
    debrief_summary: str = ""
    follow_up_actions: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("")
async def create_exercise(
    request: CreateExerciseRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Create a new exercise in available status. If scenario_catalog_id is
    provided, copy CTEP fields from the catalog row."""
    exercise_id = str(uuid.uuid4())

    result = await db.execute(
        select(Scenario).where(Scenario.id == request.scenario_catalog_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario {request.scenario_catalog_id} not found",
        )
    overview = copy.deepcopy(scenario.exercise_overview or {})
    guidelines = copy.deepcopy(scenario.exercise_guidelines or [])
    modules = copy.deepcopy(scenario.modules or [])
    success_criteria = copy.deepcopy(scenario.success_criteria or [])
    hotwash = copy.deepcopy(scenario.hotwash or {})
    appendices = copy.deepcopy(scenario.appendices or {})
    for module in modules:
        for inject in module.get("injects", []) or []:
            inject.pop("released_at", None)

    exercise = Exercise(
        id=exercise_id,
        title=request.title,
        scenario_type=scenario.scenario_type or "",
        status=ExerciseStatus.AVAILABLE,
        scenario_catalog_id=request.scenario_catalog_id,
        exercise_overview=overview,
        exercise_guidelines=guidelines,
        modules=modules,
        success_criteria=success_criteria,
        hotwash=hotwash,
        appendices=appendices,
        participants=[p.model_dump() for p in request.participants],
    )
    db.add(exercise)
    await db.commit()

    logger.info(f"Exercise {exercise_id} created in available status")
    return {
        "exercise_id": exercise_id,
        "title": request.title,
        "status": "available",
        "message": "Exercise created.",
    }


@router.get("")
async def list_exercises(
    include_archived: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """List exercises. Defaults to non-archived; pass ?include_archived=true
    to include archived rows alongside the rest.

    Each row carries derived fields used by the admin table view:
    `source_scenario_title` (joined from the catalog row, null if the
    catalog row was deleted), `participant_count`, `active_duration_minutes`
    (active time net of pauses; null until /start), `slide_position` and
    `slide_total` (1-based position in the deck; null until /start).
    """
    stmt = (
        select(Exercise, Scenario.title.label("source_scenario_title"))
        .outerjoin(Scenario, Exercise.scenario_catalog_id == Scenario.id)
        .order_by(Exercise.created_at.desc())
    )
    if not include_archived:
        stmt = stmt.where(Exercise.archived.is_(False))
    result = await db.execute(stmt)
    rows = list(result.all())

    items: List[Dict[str, Any]] = []
    for exercise, source_title in rows:
        metrics = _compute_metrics(exercise)
        slide_position, slide_total = _slide_progress(exercise)
        items.append({
            "id": exercise.id,
            "title": exercise.title,
            "scenario_type": exercise.scenario_type,
            "status": exercise.status,
            "scenario_catalog_id": exercise.scenario_catalog_id,
            "source_scenario_title": source_title,
            "participant_count": len(exercise.participants or []),
            "active_duration_minutes": metrics["active_duration_minutes"],
            "slide_position": slide_position,
            "slide_total": slide_total,
            "created_at": _as_aware(exercise.created_at).isoformat(),
            "started_at": _iso(exercise.started_at),
            "completed_at": _iso(exercise.completed_at),
            "archived": exercise.archived,
            "archived_at": _iso(exercise.archived_at),
        })
    return {"count": len(items), "exercises": items}


def _slide_progress(exercise: Exercise) -> Tuple[Optional[int], Optional[int]]:
    """Return (1-based current position, total slides) for the list view.

    Returns (None, None) for unlaunched exercises. For complete exercises
    where `current_slide` is null, returns (total, total). Unknown slide
    IDs (catalog edited after launch) report position as None but total
    is still meaningful.
    """
    if not exercise.modules:
        return None, None
    deck = _compute_deck(exercise.modules or [])
    total = len(deck)
    if not exercise.current_slide:
        if exercise.status in (ExerciseStatus.DEBRIEF, ExerciseStatus.COMPLETE):
            return total, total
        return None, None
    try:
        position = deck.index(exercise.current_slide) + 1
    except ValueError:
        return None, total
    return position, total


def _as_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite strips tzinfo on roundtrip; restore UTC for safe arithmetic with aware datetimes."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    """ISO-8601 with UTC offset. Naive datetimes (from SQLite roundtrip) are assumed UTC."""
    aware = _as_aware(dt)
    return aware.isoformat() if aware else None


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify_title(title: str) -> str:
    """Turn an exercise title into a filesystem-safe slug.

    Only `[a-z0-9-]` survive; everything else collapses to a single `-`.
    Result is trimmed of leading/trailing `-` and capped at 60 chars. Returns
    an empty string when the input has no alphanumerics — callers must have
    a fallback (the export endpoint uses the exercise id).
    """
    slug = _SLUG_RE.sub("-", title.lower()).strip("-")
    return slug[:60]


def _minutes_between(start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
    start = _as_aware(start)
    end = _as_aware(end)
    if not start or not end:
        return None
    return int((end - start).total_seconds() // 60)


def _compute_paused_seconds(ex: Exercise, now: datetime) -> int:
    total = ex.paused_total_seconds or 0
    paused_at = _as_aware(ex.paused_at)
    if ex.status == ExerciseStatus.PAUSED and paused_at:
        total += int((now - paused_at).total_seconds())
    return total


def _compute_metrics(ex: Exercise) -> Dict[str, Optional[int]]:
    now = datetime.now(timezone.utc)
    if ex.debrief_started_at:
        active_end = ex.debrief_started_at
    elif ex.completed_at:
        active_end = ex.completed_at
    elif ex.status in (ExerciseStatus.IN_PROGRESS, ExerciseStatus.PAUSED):
        active_end = now
    else:
        active_end = None
    paused_minutes = _compute_paused_seconds(ex, now) // 60
    active_raw = _minutes_between(ex.started_at, active_end)
    active_net = max(active_raw - paused_minutes, 0) if active_raw is not None else None
    return {
        "active_duration_minutes": active_net,
        "paused_duration_minutes": paused_minutes,
        "debrief_duration_minutes": _minutes_between(ex.debrief_started_at, ex.completed_at),
        "total_duration_minutes": _minutes_between(ex.created_at, ex.completed_at),
    }


def _compute_deck(modules: List[Dict[str, Any]]) -> List[str]:
    """Return the deterministic slide ID sequence for an exercise's modules.

    Format:
        ["ground_rules",
         "module:0", "inject:0:1", "inject:0:2", ...,
         "module:1", "inject:1:1", ...,
         "hotwash"]

    Module index is the 0-based position in the modules array (stable across
    edits to `module.number`). Inject token is the inject's actual `sequence`
    value (which may be non-contiguous).
    """
    deck = ["ground_rules"]
    for m_idx, module in enumerate(modules or []):
        deck.append(f"module:{m_idx}")
        injects = sorted(
            module.get("injects", []) or [],
            key=lambda i: i.get("sequence", 0),
        )
        for inject in injects:
            deck.append(f"inject:{m_idx}:{inject.get('sequence')}")
    deck.append("hotwash")
    return deck


def _parse_slide_id(slide_id: str) -> Tuple[str, Optional[int], Optional[int]]:
    """Decompose a slide ID into (kind, module_idx, sequence).

    kind ∈ {"ground_rules", "module", "inject", "hotwash"}
    For "ground_rules"/"hotwash": module_idx and sequence are None.
    For "module": sequence is None.

    Raises HTTPException(400) if the ID is malformed.
    """
    if slide_id in ("ground_rules", "hotwash"):
        return slide_id, None, None
    parts = slide_id.split(":")
    if parts[0] == "module" and len(parts) == 2:
        try:
            return "module", int(parts[1]), None
        except ValueError:
            pass
    if parts[0] == "inject" and len(parts) == 3:
        try:
            return "inject", int(parts[1]), int(parts[2])
        except ValueError:
            pass
    raise HTTPException(status_code=400, detail=f"Malformed slide_id: {slide_id!r}")


def _require_launched(exercise: Exercise) -> None:
    """Raise 400 if the exercise can't accept presentation control commands."""
    if exercise.archived:
        raise HTTPException(status_code=400, detail="Cannot present an archived exercise.")
    if exercise.current_slide is None:
        raise HTTPException(
            status_code=400,
            detail="Exercise has not been launched (call /start first).",
        )


def _require_running(exercise: Exercise) -> None:
    """Raise 400 if the exercise's status isn't in_progress or paused.

    Used by mutating endpoints. Read-only endpoints only need _require_launched.
    """
    _require_launched(exercise)
    if exercise.status not in (ExerciseStatus.IN_PROGRESS, ExerciseStatus.PAUSED):
        raise HTTPException(
            status_code=400,
            detail=f"Exercise status must be in_progress or paused (current: {exercise.status}).",
        )


def _require_navigable(exercise: Exercise) -> None:
    """Raise 400 unless the exercise can accept slide-navigation commands.

    Navigation (next/previous/goto) is allowed in in_progress, paused, and
    debrief — the last so the facilitator can page back through visited slides
    to review during the hotwash debrief. Content mutation stays gated by
    _require_running.
    """
    _require_launched(exercise)
    if exercise.status not in (
        ExerciseStatus.IN_PROGRESS,
        ExerciseStatus.PAUSED,
        ExerciseStatus.DEBRIEF,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Exercise status must be in_progress, paused, or debrief "
                f"(current: {exercise.status})."
            ),
        )


def _locate_inject(
    modules: List[Dict[str, Any]], module_idx: int, sequence: int
) -> Dict[str, Any]:
    """Return the inject dict at (module_idx, sequence). 404 if missing.

    Mutations to the returned dict will be reflected when `modules` is
    written back to `exercise.modules` (the caller is responsible for
    using a deep copy and reassigning).
    """
    if module_idx < 0 or module_idx >= len(modules):
        raise HTTPException(status_code=404, detail=f"Module {module_idx} not found")
    for inj in modules[module_idx].get("injects", []) or []:
        if inj.get("sequence") == sequence:
            return inj
    raise HTTPException(
        status_code=404,
        detail=f"Inject (module {module_idx}, sequence {sequence}) not found",
    )


def _exercise_to_dict(
    exercise: Exercise,
    source_scenario_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Serialize an Exercise row to the response/export shape.

    Shared by GET /exercises/{id} and POST /exercises/{id}/export so the
    two surfaces stay aligned.
    """
    return {
        "id": exercise.id,
        "title": exercise.title,
        "scenario_type": exercise.scenario_type,
        "status": exercise.status,
        "scenario_catalog_id": exercise.scenario_catalog_id,
        "source_scenario_title": source_scenario_title,
        "current_slide": exercise.current_slide,
        "furthest_slide": exercise.furthest_slide,
        "exercise_overview": exercise.exercise_overview or {},
        "exercise_guidelines": exercise.exercise_guidelines or [],
        "modules": exercise.modules or [],
        "success_criteria": exercise.success_criteria or [],
        "hotwash": exercise.hotwash or {},
        "appendices": exercise.appendices or {},
        "participants": exercise.participants or [],
        "created_at": _as_aware(exercise.created_at).isoformat(),
        "started_at": _iso(exercise.started_at),
        "debrief_started_at": _iso(exercise.debrief_started_at),
        "paused_at": _iso(exercise.paused_at),
        "paused_total_seconds": exercise.paused_total_seconds or 0,
        "completed_at": _iso(exercise.completed_at),
        "archived": exercise.archived,
        "archived_at": _iso(exercise.archived_at),
        "debrief_summary": exercise.debrief_summary or "",
        "follow_up_actions": exercise.follow_up_actions or [],
        "metrics": _compute_metrics(exercise),
    }


@router.get("/{exercise_id}")
async def get_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get full exercise detail. Injects live under modules[*].injects[*]."""
    exercise = await _get_or_404(db, exercise_id)
    title = await _source_scenario_title(db, exercise)
    return _exercise_to_dict(exercise, source_scenario_title=title)


EXERCISE_REPORTS_DIR = Path("exercise_reports")
EXPORT_PACKAGE_VERSION = 1


@router.post("/{exercise_id}/export")
async def export_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Write a JSON Completion Package to ./exercise_reports/.

    Only allowed when status == complete. The file is named
    exercise-<slug>-<YYYYMMDD>-<HHMMSS>.json where <slug> is derived from
    the title and sanitized to [a-z0-9-]. Existing names receive a -2,
    -3, etc. suffix before .json. Returns the on-disk path.
    """
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status != ExerciseStatus.COMPLETE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Only completed exercises can be exported "
                f"(current status: {exercise.status})."
            ),
        )

    slug = _slugify_title(exercise.title) or exercise.id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    EXERCISE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    source_title = await _source_scenario_title(db, exercise)
    payload = {
        "package_version": EXPORT_PACKAGE_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exercise": _exercise_to_dict(exercise, source_scenario_title=source_title),
    }
    data = json.dumps(payload, indent=2, ensure_ascii=False)
    suffix = 1
    while True:
        name_suffix = "" if suffix == 1 else f"-{suffix}"
        filename = f"exercise-{slug}-{timestamp}{name_suffix}.json"
        out_path = EXERCISE_REPORTS_DIR / filename
        try:
            with out_path.open("x", encoding="utf-8") as output:
                bytes_written = output.write(data)
            break
        except FileExistsError:
            suffix += 1

    logger.info(f"Exported exercise {exercise.id} to {out_path}")
    return {
        "filename": filename,
        "path": str(out_path),
        "bytes_written": bytes_written,
    }


@router.post("/{exercise_id}/start")
async def start_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Launch. Stamps started_at and seeds presentation pointers at 'ground_rules'."""
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status != ExerciseStatus.AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail=f"Exercise must be available before starting (current: {exercise.status})",
        )
    exercise.status = ExerciseStatus.IN_PROGRESS
    exercise.started_at = datetime.now(timezone.utc)
    exercise.current_slide = "ground_rules"
    exercise.furthest_slide = "ground_rules"
    await db.commit()
    return {"exercise_id": exercise_id, "status": "in_progress", "message": "Exercise started."}



@router.post("/{exercise_id}/pause")
async def pause_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Pause an in-progress exercise. Stamps paused_at."""
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status != ExerciseStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause exercise from status '{exercise.status}' (must be in_progress)",
        )
    exercise.status = ExerciseStatus.PAUSED
    exercise.paused_at = datetime.now(timezone.utc)
    await db.commit()
    return {"exercise_id": exercise_id, "status": "paused", "message": "Exercise paused."}


@router.post("/{exercise_id}/resume")
async def resume_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Resume a paused exercise. Adds elapsed pause time to paused_total_seconds, clears paused_at."""
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status != ExerciseStatus.PAUSED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume exercise from status '{exercise.status}' (must be paused)",
        )
    paused_at = _as_aware(exercise.paused_at)
    if paused_at:
        elapsed = (datetime.now(timezone.utc) - paused_at).total_seconds()
        exercise.paused_total_seconds = (exercise.paused_total_seconds or 0) + int(elapsed)
    exercise.paused_at = None
    exercise.status = ExerciseStatus.IN_PROGRESS
    await db.commit()
    return {
        "exercise_id": exercise_id,
        "status": "in_progress",
        "paused_total_seconds": exercise.paused_total_seconds,
        "message": "Exercise resumed.",
    }


@router.post("/{exercise_id}/complete")
async def complete_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Mark complete. Only allowed from debrief."""
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status != ExerciseStatus.DEBRIEF:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete exercise from status '{exercise.status}' (must be debrief)",
        )
    exercise.status = ExerciseStatus.COMPLETE
    exercise.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"exercise_id": exercise_id, "status": "complete", "message": "Exercise complete."}


@router.post("/{exercise_id}/archive")
async def archive_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Archive an exercise. Idempotent. Auto-pauses an in-progress exercise so its active timer freezes while archived."""
    exercise = await _get_or_404(db, exercise_id)
    if not exercise.archived:
        now = datetime.now(timezone.utc)
        if exercise.status == ExerciseStatus.IN_PROGRESS:
            exercise.status = ExerciseStatus.PAUSED
            exercise.paused_at = now
        exercise.archived = True
        exercise.archived_at = now
        await db.commit()
    return {
        "exercise_id": exercise_id,
        "status": exercise.status,
        "archived": True,
        "archived_at": _iso(exercise.archived_at),
    }


@router.post("/{exercise_id}/unarchive")
async def unarchive_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Unarchive. Idempotent."""
    exercise = await _get_or_404(db, exercise_id)
    if exercise.archived:
        exercise.archived = False
        exercise.archived_at = None
        await db.commit()
    return {"exercise_id": exercise_id, "archived": False}


@router.delete("/{exercise_id}")
async def delete_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Hard-delete an exercise. Irreversible.

    Refused while the exercise is in progress — pause or complete it first so a
    running exercise can't be deleted out from under the facilitator.
    """
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status == ExerciseStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an in-progress exercise. Pause or complete it first.",
        )
    await db.delete(exercise)
    await db.commit()
    return {"exercise_id": exercise_id, "deleted": True}


@router.put("/{exercise_id}/debrief")
async def update_debrief(
    exercise_id: str,
    request: DebriefRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Save debrief notes. Permitted in status debrief or complete."""
    exercise = await _get_or_404(db, exercise_id)
    if exercise.status not in (ExerciseStatus.DEBRIEF, ExerciseStatus.COMPLETE):
        raise HTTPException(
            status_code=400,
            detail=f"Debrief notes only editable in status debrief/complete (current: {exercise.status})",
        )
    exercise.debrief_summary = request.debrief_summary
    exercise.follow_up_actions = request.follow_up_actions
    await db.commit()
    return {
        "exercise_id": exercise_id,
        "debrief_summary": exercise.debrief_summary,
        "follow_up_actions": exercise.follow_up_actions,
    }


@router.post("/{exercise_id}/present/next")
async def present_next(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Advance current_slide one position. Stamps released_at on injects the
    first time they are shown. Arriving at hotwash begins the debrief."""
    exercise = await _get_or_404(db, exercise_id)
    _require_navigable(exercise)

    deck = _compute_deck(exercise.modules or [])
    try:
        current_idx = deck.index(exercise.current_slide)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=f"current_slide {exercise.current_slide!r} not in computed deck",
        )

    if current_idx + 1 >= len(deck):
        # Already on the last slide (hotwash); debrief was entered on arrival.
        return {
            "exercise_id": exercise_id,
            "status": exercise.status,
            "current_slide": exercise.current_slide,
            "message": "Already at the final slide.",
        }

    next_slide = deck[current_idx + 1]
    exercise.current_slide = next_slide
    current_furthest_idx = (
        deck.index(exercise.furthest_slide)
        if exercise.furthest_slide in deck
        else -1
    )
    if (current_idx + 1) > current_furthest_idx:
        exercise.furthest_slide = next_slide

    # Arriving at hotwash for the first time begins the debrief.
    if next_slide == "hotwash" and exercise.status in (
        ExerciseStatus.IN_PROGRESS,
        ExerciseStatus.PAUSED,
    ):
        now = datetime.now(timezone.utc)
        if exercise.status == ExerciseStatus.PAUSED:
            paused_at = _as_aware(exercise.paused_at)
            if paused_at:
                elapsed = (now - paused_at).total_seconds()
                exercise.paused_total_seconds = (
                    (exercise.paused_total_seconds or 0) + int(elapsed)
                )
            exercise.paused_at = None
        exercise.status = ExerciseStatus.DEBRIEF
        exercise.debrief_started_at = now

    # If the next slide is an inject, stamp released_at when newly shown.
    kind, m_idx, seq = _parse_slide_id(next_slide)
    if kind == "inject":
        modules = copy.deepcopy(exercise.modules or [])
        target = modules[m_idx]
        for inj in target.get("injects", []):
            if inj.get("sequence") == seq:
                if not inj.get("released_at"):
                    inj["released_at"] = datetime.now(timezone.utc).isoformat()
                break
        exercise.modules = modules

    await db.commit()
    return {
        "exercise_id": exercise_id,
        "status": exercise.status,
        "current_slide": next_slide,
        "furthest_slide": exercise.furthest_slide,
    }


@router.post("/{exercise_id}/present/previous")
async def present_previous(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Move current_slide back one position. No-op at ground_rules.
    Never un-releases, never moves furthest_slide."""
    exercise = await _get_or_404(db, exercise_id)
    _require_navigable(exercise)

    if exercise.current_slide == "ground_rules":
        return {
            "exercise_id": exercise_id,
            "current_slide": exercise.current_slide,
            "message": "Already at first slide.",
        }

    deck = _compute_deck(exercise.modules or [])
    try:
        current_idx = deck.index(exercise.current_slide)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=f"current_slide {exercise.current_slide!r} not in computed deck",
        )

    exercise.current_slide = deck[current_idx - 1]
    await db.commit()
    return {"exercise_id": exercise_id, "current_slide": exercise.current_slide}


class GotoRequest(BaseModel):
    slide_id: str


class RevealRequest(BaseModel):
    module_idx: int
    sequence: int
    question_idx: int


class InjectPatchRequest(BaseModel):
    module_idx: int
    sequence: int
    expected_actions_checked: Optional[List[int]] = None
    facilitator_notes: Optional[str] = None


@router.post("/{exercise_id}/present/goto")
async def present_goto(
    exercise_id: str,
    request: GotoRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Jump to a previously-visited slide. Rejects forward jumps."""
    exercise = await _get_or_404(db, exercise_id)
    _require_navigable(exercise)

    deck = _compute_deck(exercise.modules or [])
    if request.slide_id not in deck:
        raise HTTPException(
            status_code=400, detail=f"Unknown slide_id: {request.slide_id!r}"
        )

    target_idx = deck.index(request.slide_id)
    furthest_idx = (
        deck.index(exercise.furthest_slide)
        if exercise.furthest_slide in deck
        else 0
    )
    if target_idx > furthest_idx:
        raise HTTPException(
            status_code=400,
            detail="Cannot jump forward past furthest_slide; only backward jumps to visited slides are allowed.",
        )

    exercise.current_slide = request.slide_id
    await db.commit()
    return {"exercise_id": exercise_id, "current_slide": exercise.current_slide}


@router.post("/{exercise_id}/present/reveal")
async def present_reveal(
    exercise_id: str,
    request: RevealRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Mark a discussion question revealed on the named inject. Idempotent."""
    exercise = await _get_or_404(db, exercise_id)
    _require_running(exercise)

    modules = copy.deepcopy(exercise.modules or [])
    inj = _locate_inject(modules, request.module_idx, request.sequence)

    questions = inj.get("discussion_questions") or []
    if request.question_idx < 0 or request.question_idx >= len(questions):
        raise HTTPException(
            status_code=404,
            detail=f"question_idx {request.question_idx} out of range (have {len(questions)} questions)",
        )

    revealed = inj.setdefault("revealed_questions", [])
    if request.question_idx not in revealed:
        revealed.append(request.question_idx)

    exercise.modules = modules
    await db.commit()
    return {
        "exercise_id": exercise_id,
        "module_idx": request.module_idx,
        "sequence": request.sequence,
        "revealed_questions": revealed,
    }


@router.patch("/{exercise_id}/present/inject")
async def present_patch_inject(
    exercise_id: str,
    request: InjectPatchRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Patch the per-inject runtime state. Either field may be omitted."""
    exercise = await _get_or_404(db, exercise_id)
    _require_running(exercise)

    modules = copy.deepcopy(exercise.modules or [])
    inj = _locate_inject(modules, request.module_idx, request.sequence)

    if request.expected_actions_checked is not None:
        actions = inj.get("expected_actions") or []
        for idx in request.expected_actions_checked:
            if idx < 0 or idx >= len(actions):
                raise HTTPException(
                    status_code=400,
                    detail=f"expected_actions_checked contains out-of-range index {idx}",
                )
        # Deduplicate + preserve order from the client.
        seen: set[int] = set()
        inj["expected_actions_checked"] = [
            i for i in request.expected_actions_checked
            if not (i in seen or seen.add(i))
        ]

    if request.facilitator_notes is not None:
        inj["facilitator_notes"] = request.facilitator_notes

    exercise.modules = modules
    await db.commit()
    return {
        "exercise_id": exercise_id,
        "module_idx": request.module_idx,
        "sequence": request.sequence,
        "expected_actions_checked": inj.get("expected_actions_checked", []),
        "facilitator_notes": inj.get("facilitator_notes", ""),
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _source_scenario_title(db: AsyncSession, exercise: Exercise) -> Optional[str]:
    """Return the catalog scenario's title, or None if it was deleted."""
    if not exercise.scenario_catalog_id:
        return None
    result = await db.execute(
        select(Scenario.title).where(Scenario.id == exercise.scenario_catalog_id)
    )
    return result.scalar_one_or_none()


async def _get_or_404(db: AsyncSession, exercise_id: str) -> Exercise:
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    return exercise
