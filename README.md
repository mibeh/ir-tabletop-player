# IR Tabletop Player

IR Tabletop Player stores scenarios aligned with [CISA's Tabletop Exercise Packages (CTEPs)](https://www.cisa.gov/resources-tools/services/cisa-tabletop-exercise-packages) and runs facilitator-led incident response tabletop exercises. It includes an admin UI, separate facilitator and presenter views, and skills for creating scenarios and after-action reports.

## Quick start

You need Python 3.10 or newer and [uv](https://docs.astral.sh/uv/). The browser also needs access to `esm.sh`, which serves the UI's lit-html module.

The app has no built-in authentication. `server.py` listens on all network interfaces by default, so bind it to the loopback interface for local use:

```bash
git clone https://github.com/mibeh/ir-tabletop-player.git
cd ir-tabletop-player
uv sync
uv run python server.py --host 127.0.0.1
```

Open the [admin UI](http://localhost:8001). The [API documentation](http://localhost:8001/docs) and [health endpoint](http://localhost:8001/health) are also available. For development reloads, add `--reload` to the server command.

## Run an exercise

1. Create a compatible scenario JSON with the included [scenario generator skill](skills/ttx-scenario-generator/SKILL.md), or bring an existing CTEP-aligned JSON file. The skill saves new scenarios under `skills/ttx-scenario-generator/scenarios_output/`.
2. In the admin UI, open **Scenarios**, select the JSON file under **Upload Scenario JSON**, and click **Upload**.
3. Open **Exercises** → **New Exercise**. Enter a title, select the uploaded scenario, and add at least one participant. Each participant needs a name, position, exercise role, and department.
4. Open the exercise and click **Begin Exercise**. This opens the facilitator and presenter views. The facilitator advances the slides and can record notes, reveal questions, and check expected actions.
5. Advancing **onto** the hotwash slide starts debrief. Record the debrief summary and follow-up actions in the facilitator view, then click **Complete Exercise**.
6. In the completed exercise's admin view, click **Download Package**. This writes a completion-package JSON file on the **server** under `exercise_reports/`; it does not trigger a browser download.

An exercise moves through `available → in_progress ⇄ paused → debrief → complete`. The presenter can browse completed exercises. Archiving is separate from status; archived exercises are hidden from the list unless **Show archived** is selected.

## Scenario and report files

| Artifact | Location | How it is made |
|---|---|---|
| Scenario JSON | `skills/ttx-scenario-generator/scenarios_output/<scenario_id>.json` | The [scenario generator skill](skills/ttx-scenario-generator/SKILL.md) creates it; upload it through **Scenarios**. |
| Completion-package JSON | `exercise_reports/exercise-*.json` | **Download Package** writes it after the exercise is complete. |
| After-action report DOCX | `skills/ttx-report-generator/reports/aar-*.docx` | The [report generator skill](skills/ttx-report-generator/SKILL.md) analyzes the scenario and completion package, then renders a report. |

The report skill can also use a Teams or Zoom `.vtt` transcript when available. Without one, it must state the evidence limit and cannot infer what participants said. Its `render_aar.py` script takes an authored findings JSON, not a raw completion package.

These output directories and the local SQLite database are ignored by Git. The files remain on disk until you remove them.

## Configuration and storage

`DATABASE_URL` can be set in the environment or in a `.env` file at the project root. It defaults to `sqlite+aiosqlite:///./ir_tabletop.db`, relative to the directory from which you start the server. No configuration file is needed for local use.

`server.py` currently sets logging to `INFO`. Although `src/config.py` defines a `LOG_LEVEL` setting, the server does not apply it.

The database has two tables: `scenarios` holds reusable templates, and `exercises` holds the selected scenario's copied content, participant roster, presentation state, and debrief data. JSON fields are stored through SQLAlchemy's `JSON` type.

## API and scenario format

The interactive [API documentation](http://localhost:8001/docs) is the full endpoint reference. The main workflow uses:

| Method and path | Purpose |
|---|---|
| `POST /scenarios` | Upload one or more JSON files using repeated `files` multipart fields. The response reports success or failure for each file. |
| `POST /exercises` | Create an exercise from a `scenario_catalog_id`, title, and participant roster. |
| `POST /exercises/{id}/present/next` | Advance the deck, release injects on first visit, and enter debrief on arrival at hotwash. |
| `PUT /exercises/{id}/debrief` | Save the debrief summary and follow-up actions. |
| `POST /exercises/{id}/complete` | Complete an exercise in debrief. |
| `POST /exercises/{id}/export` | Write the completion package for a completed exercise. |

Scenario JSON requires `scenario_id`, `metadata`, `exercise_overview`, `scenario_details`, and a nonempty `modules` array. Every module needs a nonempty `injects` array. The `scenario_id` format is `ttx-YYYY-MM-DD-NN`; `metadata.framing`, when present, must be `internal` or `vendor-responsibility`. See the [scenario schema](skills/ttx-scenario-generator/references/scenario-schema.md) for the full structure.

For uploads, invalid JSON, invalid structure, and duplicate IDs appear as failed entries in the per-file response; other files in the batch can still succeed. An empty upload returns HTTP `400`. Changing a scenario ID with `PUT /scenarios/{id}` to one used by another scenario returns HTTP `409`.

## Development

### Tests

Tests use a temporary SQLite database, separate from `ir_tabletop.db`. Backend tests use httpx with ASGITransport; UI tests use Playwright and a local Uvicorn process.

```bash
uv sync --extra test
uv run playwright install chromium   # one-time browser install
uv run pytest                         # full suite
uv run pytest tests/api               # backend
uv run pytest -m ui                   # browser UI
```

### Database migrations

[Alembic](https://alembic.sqlalchemy.org/) manages the schema. Server startup applies pending migrations automatically.

```bash
uv run alembic current
uv run alembic history
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Inspect autogenerated migrations before committing them.

### Project layout

- [`api/routes/`](api/routes/) contains the scenario, exercise, and presentation endpoints.
- [`api/static/`](api/static/) contains the admin, presenter, and facilitator pages. The UI uses lit-html without a build step.
- [`src/models/`](src/models/) defines the two SQLAlchemy tables; [`src/config.py`](src/config.py) and [`src/database.py`](src/database.py) handle settings and database setup.
- [`alembic/`](alembic/) contains schema migrations.
- [`skills/`](skills/) contains the scenario and report generator instructions and renderer.
- [`tests/`](tests/) contains API, UI, and skill tests.

Code uses absolute imports such as `from src.database import ...`. Run from the project root with `uv run` so those imports resolve. Schema changes go through Alembic.

## Contributing

Create a feature branch, run the relevant tests above, and submit a pull request against `main`.
