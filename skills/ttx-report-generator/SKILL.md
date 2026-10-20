---
name: ttx-report-generator
description: Generate a CTEP-format After-Action Report / Improvement Plan (AAR/IP) as a Word (.docx) document from a tabletop exercise that has already been run. Takes three inputs — the scenario JSON (the plan), the exercise completion-package JSON exported by the platform (the runtime record), and the Teams/Zoom .vtt call transcript (what participants actually said) — and produces the AAR/IP. Use this skill whenever the user asks to create, write, generate, or build an after-action report, AAR, AAR/IP, improvement plan, hotwash report, or post-exercise report for a TTX, tabletop, or IR exercise; or wants to analyze, evaluate, or write up how a tabletop exercise went. Distinct from ttx-scenario-generator, which produces the scenario before the exercise; this skill reports on it afterward.
---

# TTX Report Generator

This skill turns a **run** tabletop exercise into a CTEP-format After-Action
Report / Improvement Plan (AAR/IP) DOCX, with no organization-specific
branding. It is the analytical counterpart to `ttx-scenario-generator`: that
skill produces the plan; this one reports on how the exercise went.

You (the model) do the analysis and author a structured **findings JSON**; a
bundled script renders it deterministically to a Word document.

## Inputs

Ask the user for three files (accept whatever they provide; degrade gracefully
if one is missing):

1. **Scenario JSON** — the `ttx-scenario-generator` output (the plan / answer
   key: objectives, expected actions, discussion questions).
2. **Completion-package JSON** — `exercise_reports/exercise-*.json` exported by
   the platform (runtime record: timing metrics, inject `released_at`,
   `expected_actions_checked`, facilitator notes, hotwash, debrief summary,
   follow-up actions, participants).
3. **Call transcript** — a Teams/Zoom `.vtt` of the exercise discussion.

The completion package already embeds the scenario content; use the separate
scenario JSON as the pristine answer key.

## Workflow

### 1. Parse the transcript

Run the parser to normalize the `.vtt` into speaker turns:

```bash
uv run python -c "import sys, json; \
sys.path.insert(0, 'skills/ttx-report-generator/scripts'); \
from vtt_parser import parse_vtt; \
cues=parse_vtt(open(sys.argv[1]).read()); \
print(json.dumps([c.__dict__ for c in cues], indent=2))" path/to/transcript.vtt
```

### 2. Correlate (hybrid)

Map discussion to the exercise structure:

- When injects carry `released_at` timestamps, use them with the cue times to
  segment the transcript into per-inject windows.
- Otherwise (or for fine-grained mapping), reason by content to attach
  discussion to specific objectives, `expected_actions`, and
  `discussion_questions`.

### 3. Analyze

For each exercise objective:

- Map it to one or more **Core Capabilities** (see
  `references/aar-template.md` for the cyber-relevant list).
- Identify **Strengths** — grounded in what participants actually said.
- Identify **Areas for Improvement** — each an Observation with a Priority
  (`Critical`, `High`, `Medium`, or `Low`), Reference, Analysis, and
  Recommendation. Compare actual responses against the scenario's
  `expected_actions` and the package's `expected_actions_checked`.

Then build the **Improvement Plan** rows (seeded from `follow_up_actions` plus
gaps you surfaced): issue, priority, corrective action, capability element,
responsible org, POC, and dates. Carry the priority through from the matching
Area for Improvement.

Finally, write the **Executive Summary**: a short narrative for a leadership
reader that frames the exercise objectives and summarizes the headline
strengths and areas for improvement.

### 4. Author the findings JSON

Write a findings JSON matching `references/findings-schema.md`. Default the
sponsor to "IR Team" and the caveat to
"Fictional Training Exercise — Not a Real Incident". Save it to a temp path.

### 5. Render

```bash
uv run python skills/ttx-report-generator/scripts/render_aar.py /tmp/findings.json
```

The DOCX is written to `skills/ttx-report-generator/reports/aar-<slug>-<timestamp>.docx`.
Report the output path to the user and summarize: objectives analyzed, count of
strengths and areas for improvement, and improvement-plan row count. Clean up
the temp findings JSON.

## What this skill does NOT do

- It does not run the exercise or produce the scenario — that is
  `ttx-scenario-generator`.
- It does not output PDF/HTML/Markdown — DOCX only.
- It does not fetch from the live API — it works on files.
- It does not invent participant responses; every strength and gap must trace
  to the transcript.

## Reference files

- `references/findings-schema.md` — the findings JSON contract, field by field.
- `references/aar-template.md` — the document structure and visual style.
