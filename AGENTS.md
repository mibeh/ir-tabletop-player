# Repository guidance

This file provides guidance to coding agents working with code in this repository.

## What this is

IR tabletop exercise platform. Hosts a CTEP-aligned scenario catalog. Exercises are created against a participant roster and managed by a facilitator through the admin UI.

## Run / develop

```bash
# Install (uv manages the venv and locks deps in uv.lock)
uv sync

# Run — uv puts the project root on sys.path so `src.*` and `api.*` resolve
uv run python server.py
uv run python server.py --reload   # dev auto-reload

# Endpoints
# Admin UI:  http://localhost:8001
# API docs:  http://localhost:8001/docs
# Health:    http://localhost:8001/health
```

Tests live under `tests/` (backend via httpx+ASGI, UI via Playwright):

```bash
uv sync --extra test
uv run playwright install chromium    # one-time
uv run pytest                          # all
uv run pytest tests/api                # backend only (fast)
uv run pytest -m ui                    # UI only
```

No linter config or build step is checked in. Don't invent commands that aren't here.

## Architecture

Single FastAPI process (`api/app.py`) with async SQLAlchemy (SQLite by default at `./ir_tabletop.db`, configurable via `DATABASE_URL`). One static HTML page served from `api/static/` — the admin UI at `/`. Schema is managed by Alembic — `init_db()` runs `alembic upgrade head` at startup, so migrations apply automatically. Generate new migrations with `uv run alembic revision --autogenerate -m "msg"`.

### Layering

- [api/routes/](api/routes/) — request/response Pydantic models + endpoint handlers. Inject release is a side-effect of slide navigation: `/exercises/{id}/present/next` walks a deck of `ground_rules → module:N → inject:N:M → … → hotwash`; visiting an inject slide for the first time stamps `released_at` on that inject. `/present/next` from the `hotwash` slide transitions the exercise to `debrief`.
- [src/models/](src/models/) — ORM models. JSON-shaped fields on `Exercise` (`exercise_overview`, `exercise_guidelines`, `modules`, `success_criteria`, `hotwash`, `appendices`, `participants`, `follow_up_actions`) and all `Scenario` blob columns use SQLAlchemy `JSON` and are read/written as native dicts/lists.
- [src/config.py](src/config.py) — Pydantic `BaseSettings`. Reads `DATABASE_URL` and `LOG_LEVEL` from the environment; both have defaults so no `.env` is required.

### Exercise lifecycle (state machine)

`available → in_progress ⇄ paused → debrief → complete` (status values in [ExerciseStatus](src/models/exercise.py)). New exercises start in `available` with empty CTEP JSON columns; if `scenario_catalog_id` is provided at creation, the handler deep-copies `exercise_overview`, `modules`, `success_criteria`, `hotwash`, and `appendices` from the catalog row. `/start` seeds `current_slide` and `furthest_slide` at `ground_rules`. Injects live as objects under `modules[*].injects[*]`; runtime fields added during presentation include `released_at`, `revealed_questions`, `expected_actions_checked`, and `facilitator_notes`. `pause` stamps `paused_at`; `resume` accumulates elapsed pause seconds into `paused_total_seconds` (netted out of `active_duration_minutes` by `_compute_metrics`). The presentation endpoints (`/present/next`, `/previous`, `/goto`, `/reveal`, `PATCH /present/inject`) accept both `in_progress` and `paused`. `complete` is only allowed from `debrief` — there is no manual shortcut; the facilitator reaches `debrief` by advancing the deck through `hotwash`. `/present/previous` and `/goto` never regress `furthest_slide` (regression preserved by `fc76406`). Archive is orthogonal to the status machine — any exercise can be archived in any status; archiving an in-progress exercise auto-pauses it so the timer freezes. The list view hides archived rows by default (`?include_archived=true` to view); `DELETE /exercises/{id}` hard-deletes irreversibly but is refused with 409 while an exercise is `in_progress` (pause or complete it first). `POST /exercises/{id}/export` (only from `complete`) writes a versioned JSON completion package to `./exercise_reports/`; the `ttx-report-generator` skill (`skills/ttx-report-generator/scripts/render_aar.py`) is a separate CLI that renders a findings JSON into a TLP-marked after-action DOCX.

### Scenarios catalog

The platform hosts a library of reusable CTEP-aligned scenario templates produced by the external `ttx-scenario-generator` skill. CRUD lives in [api/routes/scenarios.py](api/routes/scenarios.py); the row shape is [Scenario](src/models/scenario.py) (nine SQLAlchemy `JSON` columns matching the 10 top-level CTEP keys, minus `scenario_id` which is a real `String` column). `_validate_scenario_json` enforces required top-level keys, `scenario_id` regex `^ttx-\d{4}-\d{2}-\d{2}-\d{2,}$`, and `metadata.framing ∈ {internal, vendor-responsibility}`. `POST /scenarios` accepts one or more files (repeated `files` multipart field) and returns a per-file report `{uploaded, failed, results[]}` — each result is `{filename, status: created|failed, …}`, where created entries carry `id` + `scenario_id` and failed entries carry `error`. Each file is validated and committed independently (`_process_one_file`, per-file commit, intra-batch `scenario_id` dedupe), so a bad file never blocks the rest; per-file problems (bad JSON, schema failure, duplicate id) surface as failed results rather than HTTP errors, and the only request-level error is an empty file set (400). `_apply_scenario_fields` writes both the JSON blobs and the denormalized scalar columns (`title`, `scenario_type`, `framing`, `difficulty`, `module_count`, `inject_count`) — POST and PUT both go through it, so adding a new derivable scalar means editing that helper only. PUT preserves `created_at` and re-checks `scenario_id` uniqueness against other rows when it changes. `POST /scenarios/{id}/copy` clones a scenario into a new row with a freshly minted `scenario_id` (date + next available `NN`) and a ` (Copy)` title suffix. The admin UI's "Scenarios" tab in [api/static/index.html](api/static/index.html) renders a structured form editor (modules → injects → questions → follow-ups, plus list editors for hotwash/success criteria and a by-category editor for `appendices.additional_discussion_questions`); preserved-but-uneditable sections render read-only. The editor renders via lit-html — interpolated values are auto-escaped by position, and event handlers bind to JS functions through `@click=${fn}` closures rather than inline `onclick=` strings, so user-controlled values never reach the HTML parser as code.

## Conventions specific to this repo

- **Absolute imports.** Code uses `from src.foo import bar` / `from api.routes import ...`. Run via `uv run python server.py` — uv puts the project root on `sys.path`, so no `PYTHONPATH` export is needed.
- **JSON columns use SQLAlchemy `JSON`.** Models declare list/dict columns with `mapped_column(JSON, default=list)` (or `default=dict`). Read/write native Python objects directly — no `json.loads` / `json.dumps` at the boundary. The columns still serialize to TEXT on SQLite, but SQLAlchemy handles it.
- **Schema changes go through Alembic.** Edit the model, then `uv run alembic revision --autogenerate -m "msg"`. Inspect the generated file. Migrations apply automatically at server startup.
- **Always clean up any temp files created**
