"""Scenarios catalog endpoints. Serves the admin UI Scenarios tab."""
from __future__ import annotations

import copy
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.exercise import Exercise
from src.models.scenario import Scenario

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# Required top-level keys in the uploaded JSON.
_REQUIRED_KEYS = ("scenario_id", "metadata", "exercise_overview", "scenario_details", "modules")
_SCENARIO_ID_RE = re.compile(r"^ttx-\d{4}-\d{2}-\d{2}-\d{2,}$")
_ALLOWED_FRAMINGS = {"internal", "vendor-responsibility"}


def _validate_scenario_json(data: Any) -> None:
    """Raise HTTPException(400) if the payload doesn't match the expected shape."""
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Top-level JSON must be an object.")

    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required top-level keys: {', '.join(missing)}",
        )

    scenario_id = data.get("scenario_id")
    if not isinstance(scenario_id, str) or not _SCENARIO_ID_RE.match(scenario_id):
        raise HTTPException(
            status_code=400,
            detail="scenario_id must match format 'ttx-YYYY-MM-DD-NN' (e.g. ttx-2026-05-26-01).",
        )

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise HTTPException(status_code=400, detail="'metadata' must be an object.")
    if not isinstance(data.get("scenario_details"), dict):
        raise HTTPException(status_code=400, detail="'scenario_details' must be an object.")
    if not isinstance(data.get("exercise_overview"), dict):
        raise HTTPException(status_code=400, detail="'exercise_overview' must be an object.")

    framing = metadata.get("framing")
    if framing is not None and framing not in _ALLOWED_FRAMINGS:
        raise HTTPException(
            status_code=400,
            detail=f"metadata.framing must be one of {sorted(_ALLOWED_FRAMINGS)} (got {framing!r}).",
        )

    modules = data.get("modules")
    if not isinstance(modules, list) or len(modules) < 1:
        raise HTTPException(
            status_code=400,
            detail="'modules' must be a non-empty array.",
        )
    for i, module in enumerate(modules):
        if not isinstance(module, dict):
            raise HTTPException(
                status_code=400,
                detail=f"modules[{i}] must be an object.",
            )
        injects = module.get("injects")
        if not isinstance(injects, list) or len(injects) < 1:
            raise HTTPException(
                status_code=400,
                detail=f"modules[{i}].injects must be a non-empty array.",
            )
        for j, inject in enumerate(injects):
            if not isinstance(inject, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"modules[{i}].injects[{j}] must be an object.",
                )


def _summary(s: Scenario, exercise_count: int = 0) -> Dict[str, Any]:
    """Row shape used by the list endpoint and the create response."""
    return {
        "id": s.id,
        "scenario_id": s.scenario_id,
        "title": s.title,
        "scenario_type": s.scenario_type,
        "framing": s.framing,
        "difficulty": s.difficulty,
        "module_count": s.module_count,
        "inject_count": s.inject_count,
        "exercise_count": exercise_count,
        "created_at": s.created_at.isoformat(),
    }


def _reconstitute(s: Scenario) -> Dict[str, Any]:
    """Rebuild the full CTEP JSON object from the row's JSON columns."""
    return {
        "scenario_id": s.scenario_id,
        "metadata": s.metadata_json or {},
        "exercise_overview": s.exercise_overview or {},
        "participant_roles": s.participant_roles or {},
        "exercise_guidelines": s.exercise_guidelines or [],
        "scenario_details": s.scenario_details or {},
        "modules": s.modules or [],
        "hotwash": s.hotwash or {},
        "appendices": s.appendices or {},
        "success_criteria": s.success_criteria or [],
    }


async def _get_or_404(db: AsyncSession, record_id: str) -> Scenario:
    result = await db.execute(select(Scenario).where(Scenario.id == record_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {record_id} not found")
    return scenario


async def _mint_scenario_id(db: AsyncSession) -> str:
    """Mint a new scenario_id of the form ttx-YYYY-MM-DD-NN for today's UTC date.

    NN is one greater than the highest existing NN for today, zero-padded to
    two digits. Starts at "01" if no scenarios exist for today.

    Not atomic: concurrent callers may derive the same NN. The unique
    constraint on scenario_id will surface any collision as an IntegrityError.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prefix = f"ttx-{today}-"
    result = await db.execute(
        select(Scenario.scenario_id).where(Scenario.scenario_id.like(f"{prefix}%"))
    )
    highest = 0
    for (sid,) in result.all():
        suffix = sid[len(prefix):]
        try:
            highest = max(highest, int(suffix))
        except ValueError:
            logger.warning("Non-integer scenario_id suffix skipped in _mint_scenario_id: %s", sid)
            continue
    return f"{prefix}{highest + 1:02d}"


def _apply_scenario_fields(scenario: Scenario, data: Dict[str, Any]) -> None:
    """Write all derivable fields from a validated CTEP payload onto a Scenario row.

    Used by POST (new row), PUT (update existing row), and the copy endpoint.
    `created_at` is not touched here — the caller manages it.
    """
    overview = data.get("exercise_overview") or {}
    details = data.get("scenario_details") or {}
    metadata = data.get("metadata") or {}
    modules = data.get("modules") or []

    scenario.scenario_id = data["scenario_id"]
    scenario.metadata_json = metadata
    scenario.exercise_overview = overview
    scenario.participant_roles = data.get("participant_roles") or {}
    scenario.exercise_guidelines = data.get("exercise_guidelines") or []
    scenario.scenario_details = details
    scenario.modules = modules
    scenario.hotwash = data.get("hotwash") or {}
    scenario.appendices = data.get("appendices") or {}
    scenario.success_criteria = data.get("success_criteria") or []

    scenario.title = str(overview.get("name") or details.get("title") or data["scenario_id"])
    scenario.scenario_type = str(details.get("scenario_type") or details.get("type") or "")
    scenario.framing = str(metadata.get("framing") or "")
    scenario.difficulty = str(details.get("difficulty") or "")
    scenario.module_count = len(modules) if isinstance(modules, list) else 0
    scenario.inject_count = (
        sum(len(m.get("injects", []) or []) for m in modules if isinstance(m, dict))
        if isinstance(modules, list)
        else 0
    )


async def _process_one_file(
    file: UploadFile,
    db: AsyncSession,
    batch_ids: set[str],
) -> Dict[str, Any]:
    """Validate and persist one uploaded scenario file.

    Commits the row on success. Converts every per-file problem (bad JSON,
    schema failure, duplicate id, unique-constraint race) into a failure
    result dict instead of raising. ``batch_ids`` tracks ids already created
    earlier in this same request so intra-batch duplicates are caught.
    """
    name = file.filename or "(unnamed)"
    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning("Scenario upload %s is not valid JSON: %s", name, e)
        return {"filename": name, "status": "failed", "error": "File is not valid JSON."}

    try:
        _validate_scenario_json(data)
    except HTTPException as e:
        return {"filename": name, "status": "failed", "error": str(e.detail)}

    scenario_id = data["scenario_id"]
    if scenario_id in batch_ids:
        return {"filename": name, "status": "failed",
                "error": f"Scenario {scenario_id} already exists."}
    existing = await db.execute(select(Scenario).where(Scenario.scenario_id == scenario_id))
    if existing.scalar_one_or_none() is not None:
        return {"filename": name, "status": "failed",
                "error": f"Scenario {scenario_id} already exists."}

    scenario = Scenario(created_at=datetime.now(timezone.utc))
    _apply_scenario_fields(scenario, data)
    db.add(scenario)
    try:
        await db.commit()
    except IntegrityError:
        # Only reachable on a concurrent-request race: the pre-check above
        # caught any duplicate already visible to this transaction.
        await db.rollback()
        return {"filename": name, "status": "failed",
                "error": f"Scenario {scenario_id} already exists."}
    await db.refresh(scenario)
    batch_ids.add(scenario_id)
    logger.info(f"Scenario {scenario_id} uploaded (from {name})")
    return {"filename": name, "status": "created", "id": scenario.id,
            "scenario_id": scenario.scenario_id}


@router.post("")
async def upload_scenarios(
    files: list[UploadFile] | None = File(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Upload one or more scenario JSON files from the ttx-scenario-generator skill.

    Each file is processed independently: valid files are saved, bad files are
    reported. The batch is never rejected wholesale. An empty/missing file set
    is the only request-level error (400).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    batch_ids: set[str] = set()
    results = [await _process_one_file(f, db, batch_ids) for f in files]
    uploaded = sum(1 for r in results if r["status"] == "created")
    return {"uploaded": uploaded, "failed": len(results) - uploaded, "results": results}


@router.get("")
async def list_scenarios(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Return all scenarios as summary rows, newest first.

    `exercise_count` counts every exercise linked to the scenario, including
    archived ones — archive is orthogonal to existence.
    """
    exercise_count_subq = (
        select(func.count(Exercise.id))
        .where(Exercise.scenario_catalog_id == Scenario.id)
        .correlate(Scenario)
        .scalar_subquery()
    )
    stmt = (
        select(Scenario, exercise_count_subq.label("exercise_count"))
        .order_by(Scenario.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = list(result.all())
    return {
        "count": len(rows),
        "scenarios": [_summary(s, exercise_count=int(c or 0)) for s, c in rows],
    }


@router.get("/{record_id}")
async def get_scenario(
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return the full reconstituted CTEP JSON + audit fields."""
    scenario = await _get_or_404(db, record_id)
    payload = _reconstitute(scenario)
    payload["_audit"] = {
        "id": scenario.id,
        "created_at": scenario.created_at.isoformat(),
    }
    return payload


@router.get("/{record_id}/download")
async def download_scenario(
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Return the reconstituted CTEP JSON as a downloadable file."""
    scenario = await _get_or_404(db, record_id)
    payload = _reconstitute(scenario)
    body = json.dumps(payload, indent=2)
    filename = f"{scenario.scenario_id}.json"
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{record_id}")
async def update_scenario(
    record_id: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Replace the editable fields of a scenario.

    Body shape is the full CTEP JSON (same as the upload body, no file wrapper).
    created_at is preserved.
    The body's scenario_id may differ from the existing row's scenario_id; if
    so, uniqueness is re-checked against other rows.
    """
    scenario = await _get_or_404(db, record_id)

    # Strip client-injected audit envelope if present (defensive — the editor
    # already drops it, but a hand-crafted PUT might include it).
    data = {k: v for k, v in data.items() if k != "_audit"}

    _validate_scenario_json(data)

    new_scenario_id = data["scenario_id"]
    if new_scenario_id != scenario.scenario_id:
        collision = await db.execute(
            select(Scenario).where(
                Scenario.scenario_id == new_scenario_id,
                Scenario.id != scenario.id,
            )
        )
        if collision.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Another scenario already has scenario_id {new_scenario_id!r}.",
            )

    _apply_scenario_fields(scenario, data)
    await db.commit()
    await db.refresh(scenario)

    logger.info(f"Scenario {scenario.scenario_id} updated (record {record_id})")

    payload = _reconstitute(scenario)
    payload["_audit"] = {
        "id": scenario.id,
        "created_at": scenario.created_at.isoformat(),
    }
    return payload


@router.post("/{record_id}/copy")
async def copy_scenario(
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Duplicate an existing scenario into a new row.

    The new row gets a freshly minted scenario_id (today's UTC date + next
    available NN) and a " (Copy)" suffix on the title. All JSON-blob fields
    are deep-copied. created_at is stamped at copy time.
    """
    source = await _get_or_404(db, record_id)
    new_scenario_id = await _mint_scenario_id(db)

    data = copy.deepcopy(_reconstitute(source))
    data["scenario_id"] = new_scenario_id
    data["exercise_overview"]["name"] = f"{source.title} (Copy)"

    new_scenario = Scenario(created_at=datetime.now(timezone.utc))
    _apply_scenario_fields(new_scenario, data)

    db.add(new_scenario)
    await db.commit()
    await db.refresh(new_scenario)

    logger.info(f"Scenario {record_id} copied to {new_scenario_id}")
    return _summary(new_scenario)


@router.delete("/{record_id}")
async def delete_scenario(
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Hard-delete a scenario."""
    scenario = await _get_or_404(db, record_id)
    await db.delete(scenario)
    await db.commit()
    logger.info(f"Scenario {scenario.scenario_id} deleted")
    return {"id": record_id, "deleted": True}
