"""Deterministic test-data factories.

All factories produce static output by default. Counter resets per pytest
session; date is pinned to FIXED_DATE so the same inputs round-trip across
runs.
"""
from __future__ import annotations

import json
from datetime import date
from itertools import count
from typing import Any, Dict, List

FIXED_DATE = date(2026, 1, 1)

_id_counter = count(1)


def make_scenario_id(today: date | None = None) -> str:
    """Return a scenario_id of form 'ttx-YYYY-MM-DD-NN'."""
    d = today or FIXED_DATE
    return f"ttx-{d.isoformat()}-{next(_id_counter):02d}"


def make_inject(seq: int, **overrides: Any) -> Dict[str, Any]:
    inject = {
        "sequence": seq,
        "title": f"Inject {seq}",
        "narrative": "Test narrative.",
        "discussion_questions": [
            {"question": f"Q{seq}.1", "follow_ups": ["Why?"]},
            {"question": f"Q{seq}.2", "follow_ups": []},
        ],
        "expected_actions": [f"Action {seq}.1", f"Action {seq}.2"],
    }
    inject.update(overrides)
    return inject


def make_module(order: int, inject_count: int = 2, **overrides: Any) -> Dict[str, Any]:
    module = {
        "order": order,
        "title": f"Module {order}",
        "injects": [make_inject(i + 1) for i in range(inject_count)],
    }
    module.update(overrides)
    return module


def make_scenario_json(
    *,
    scenario_id: str | None = None,
    title: str = "Smoke Test Scenario",
    scenario_type: str = "ransomware",
    framing: str = "internal",
    difficulty: str = "intermediate",
    modules: int = 2,
    injects_per_module: int = 2,
    **overrides: Any,
) -> Dict[str, Any]:
    """Return a valid CTEP scenario dict accepted by _validate_scenario_json."""
    base: Dict[str, Any] = {
        "scenario_id": scenario_id or make_scenario_id(),
        "metadata": {"framing": framing, "author": "smoke-tests"},
        "exercise_overview": {"name": title, "title": title, "summary": "Summary."},
        "scenario_details": {
            "scenario_type": scenario_type,
            "difficulty": difficulty,
        },
        "modules": [
            make_module(i + 1, injects_per_module) for i in range(modules)
        ],
        "success_criteria": [],
        "hotwash": {},
        "appendices": {},
        "participant_roles": [],
        "exercise_guidelines": [],
    }
    base.update(overrides)
    return base


def make_exercise_payload(
    *,
    scenario_catalog_id: str | None = None,
    title: str = "Smoke Test Exercise",
    participants: List[Dict[str, str]] | None = None,
    **overrides: Any,
) -> Dict[str, Any]:
    """Return a body for POST /exercises.

    Defaults to one valid participant so the payload satisfies backend
    validation (≥1 participant). Pass ``participants=[]`` to exercise the
    rejection path.
    """
    if participants is None:
        participants = [
            {
                "name": "Test User",
                "position": "Incident Commander",
                "exercise_role": "Participant",
                "department": "Security",
            }
        ]
    payload: Dict[str, Any] = {
        "title": title,
        "participants": participants,
    }
    if scenario_catalog_id is not None:
        payload["scenario_catalog_id"] = scenario_catalog_id
    payload.update(overrides)
    return payload


def expected_deck(scenario_json: Dict[str, Any]) -> List[str]:
    """Mirror api/routes/exercises.py::_compute_deck for a scenario CTEP dict.

    Returns the slide ID sequence the API will navigate through when an
    exercise is created from this scenario:
        ["ground_rules", "module:0", "inject:0:1", ..., "hotwash"]
    """
    deck: List[str] = ["ground_rules"]
    for m_idx, module in enumerate(scenario_json.get("modules", []) or []):
        deck.append(f"module:{m_idx}")
        injects = sorted(
            module.get("injects", []) or [],
            key=lambda i: i.get("sequence", 0),
        )
        for inject in injects:
            deck.append(f"inject:{m_idx}:{inject.get('sequence')}")
    deck.append("hotwash")
    return deck


def scenario_upload_files(
    *payloads: Dict[str, Any] | bytes,
    filenames: List[str] | None = None,
) -> List[tuple[str, tuple[str, bytes, str]]]:
    """Build an httpx multipart value for POST /scenarios.

    Each item is sent under the repeated ``files`` field. A dict is serialized
    to JSON; raw bytes are sent verbatim (for malformed-JSON tests).
    """
    out: List[tuple[str, tuple[str, bytes, str]]] = []
    for i, payload in enumerate(payloads):
        name = filenames[i] if filenames else f"s{i}.json"
        body = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode("utf-8")
        out.append(("files", (name, bytes(body), "application/json")))
    return out
