---
name: ttx-scenario-generator
description: Generate a realistic cyber incident response tabletop exercise (TTX) scenario tailored to the user's organization and security stack. The output follows the structure of CISA's Tabletop Exercise Package (CTEP) format — exercise overview, modules with day-based injects, inline discussion questions, hotwash, and appendix question banks — serialized to a JSON file. Use this skill whenever the user asks to create, generate, draft, or build a tabletop exercise, TTX, IR scenario, incident response exercise, security exercise, situation manual, CTEP, or training scenario. Also use when the user asks for ransomware, insider, supply-chain, or cloud-compromise scenarios for IR training, or wants to test security response playbooks against a simulated incident.
---

# TTX Scenario Generator

This skill produces a single JSON file describing a tabletop exercise scenario tailored to the user's organization. The output structure mirrors CISA's CTEP (Cybersecurity Tabletop Exercise Package) format so the resulting JSON can drive a facilitator's situation manual, an internal wiki page, or a downstream rendering pipeline.

The audience is technical: IR, SOC, security leadership, GRC, Product Security. The facilitator is also technical.

## What "good" looks like

A good TTX scenario:

- **Feels real** — uses tools and processes the user confirms are in their environment, with plausible alerts and MITRE ATT&CK techniques that match the attack chain. Tool-specific injects name real detections only when the user provides a source or confirms that it is available.
- **Reads like real telemetry** — every fabricated ID, hash, domain, username, ARN, and IP uses its real-world format. The scenario is marked fictional once in `metadata.fictional_disclaimer`, so individual values never carry `FICTIONAL`/`EXAMPLE`/`XXXX`/`<…>` placeholder tokens — see `references/scenario-schema.md` → "Make indicators look real".
- **Forces decisions** — injects expose gaps in detection, containment, communication, recovery, or legal/regulatory response. There's no single "right answer" path.
- **Is paced as modules** — typically two modules of ~60 min each, separated by a break. Each module contains multiple day-stamped injects (Day 1, Day 7, Day 30, …) that escalate the situation.
- **Aligns to NIST CSF** — questions can be mapped to Govern / Identify / Protect / Detect / Respond / Recover. Tagging questions this way helps facilitators surface coverage gaps.
- **Is self-contained** — the JSON includes enough metadata, narrative, discussion questions, facilitator notes, and references for someone else to run the exercise without further context.

Avoid implausibly cinematic threat actors, magic 0-days that bypass every control, or scenarios that resolve in one obvious step. The point is to surface ambiguity.

## Organization and security stack

Ask the user to describe the organization and its security stack before naming specific tools. Gather relevant products and services for endpoint detection, identity, cloud, email, logging, orchestration, incident tracking, backups, and privileged access, as applicable. Ask which tools are authoritative for alerts and which log sources responders can query.

If the user has not provided this context, ask a concise follow-up. Do not infer an organization's tools from a past scenario, repository contents, connected services, or familiar vendor defaults. If the user wants to proceed without sharing a stack, keep tool references generic and mark any assumptions clearly in scenario metadata. Do not reject a tool merely because it is unfamiliar or absent from a local inventory.

Use the names and capabilities the user provides. If an operational detail is uncertain, ask the user or phrase the inject as a decision the participants must resolve. Never present an assumed product, configuration, detection rule, playbook, team, tenant, or workflow as a confirmed fact.

Scenarios can focus on an internal incident, a service-provider or supplier incident, or an incident affecting customers. Confirm the intended perspective when it is unclear, and mark every scenario as fictional training content.

## Workflow

### 1. Clarify the request

If the user gave specifics (scenario type, duration, tools, difficulty, or organization context), use them. If the user has not described their security stack, ask them to list the relevant tools and systems or confirm that they prefer generic tool references. For a generic scenario request, offer the menu below and confirm only the key parameters that materially affect the scenario.

**Scenario seed options** (when no input given):

```
Which scenario would you like? (pick one or describe your own)

 1. Ransomware via phishing → endpoint encryption
 2. Insider threat — engineering data exfiltration
 3. Cloud account takeover — exposed cloud credentials
 4. Supplier compromise — compromised build pipeline or software update
 5. Business email compromise and cloud identity abuse
 6. Privileged credential theft — stolen administrator session
 7. SaaS-to-SaaS lateral movement via OAuth abuse
 8. Living-off-the-land — adversary using legitimate admin tooling
 9. APT targeting product engineering (intellectual property)
10. Detection bypass — adversary suppressing endpoint or identity alerts
11. Third-party provider compromise affecting business operations
12. Ransomware via compromised RMM at a service provider
13. Exploitation of a vulnerability in a business-critical product or service
```

**Parameters to confirm or default**:

| Parameter | Default | Notes |
|---|---|---|
| `module_count` | 2 | 1 for short (~60 min total), 2 for full (~3 hr total) |
| `module_duration_minutes` | 60 | Per module |
| `difficulty` | `medium` | low / medium / high |
| `target_audience` | mixed technical | IR, SOC, leadership, GRC, ProdSec — combination |
| `nist_csf_focus` | all six | Optionally narrow to specific functions |
| `framing` | internal | `internal` or `vendor-responsibility` |
| `scenario_name` | auto-generated | E.g., "Operation Glasshouse — Cloud Credential Exposure" |
| `output_path` | `scenarios_output/<scenario_id>.json` | Relative to this skill's directory |

Don't ask all of these. Use sensible defaults for low-impact details and record them in `metadata`. Ask about organization and stack context when it determines which tools, teams, customers, or response procedures appear in the scenario.

### 2. Gather grounding context

The goal is realism, not exhaustive research.

**External grounding (optional).** Use connected sources only when relevant, available, and authorized by the user. Ask which organizational sources may be used if this is unclear. See `references/mcp-grounding.md` for safe, targeted research guidance. Do not assume a particular MCP, repository, ticketing system, or documentation service is available.

**Detection grounding (when naming a detection rule).** If the user supplies or authorizes a detection-rule source, verify names and details there and cite only confirmed rules. Never invent a rule name, severity, or alert behavior. If no source is available, describe the alert generically or make the lack of a known detection an exercise decision point. See `references/detection-grounding.md`.

### 3. Compose the scenario

Build the scenario as a CTEP-aligned JSON document. The full schema is in `references/scenario-schema.md`. The structural backbone:

```
{
  scenario_id, metadata,
  exercise_overview {
    name,
    activity_timeline,
    purpose, nist_csf_functions, objectives,
    threat_or_hazard, scenario_summary
  }
  exercise_guidelines [...]
  scenario_details {
    title, scenario_type, difficulty, target_audience,
    threat_actor, mitre_attack,
    technologies_involved, background
  }
  modules [
    {
      number, title, duration_minutes, summary,
      injects [
        {
          day_or_time, trigger_source,
          title, narrative, indicators,
          expected_actions,
          discussion_questions [
            { category, nist_csf_function, question, follow_ups }
          ]
        }
      ]
    }
  ]
  hotwash { duration_minutes, guiding_questions }
  appendices {
    additional_discussion_questions { <category>: [...] },
    facilitator_notes { ... },
    references { ... }
  }
  success_criteria [...]
}
```

**Inject pacing** — mirror CISA's day-based pattern. A two-module exercise typically uses ~7-10 injects spread across days like Day 1, Day 7, Day 30, Day 31-morning, Day 31-afternoon, Day 33, Day 50. Each inject has 2-5 inline discussion questions tied to that moment.

**Discussion questions** — each gets:

- `category` from the CISA-aligned list: `Cyber Resilience`, `Accounts & Privileges`, `Incident Identification`, `Incident Response`, `Recovery`, `Training & Exercises`, `Senior Leaders`, `Public Information`, `Legal`, `Product Security`, `Communications`, `Detection`, `Triage`, `Containment`, `Eradication`, `Post-incident`. Pick whichever fits.
- `nist_csf_function` — one of `Govern`, `Identify`, `Protect`, `Detect`, `Respond`, `Recover`.
- `question` — open-ended.
- `follow_ups` — array of sub-questions (CISA pattern: a main question with 2-4 drill-down probes).

Examples of the pattern:

```json
{
  "category": "Incident Response",
  "nist_csf_function": "Respond",
  "question": "How are third-party vendors involved in your incident response?",
  "follow_ups": [
    "How is this documented in your CIRP?",
    "What does your service-level agreement include regarding incident response activity?"
  ]
}
```

**Appendix question bank** — `references/question-bank.md` contains a generic CISA-derived library of additional discussion questions. Adapt questions to the user's organization and confirmed security stack. Keep ~20-40 questions across relevant categories.

**MITRE ATT&CK** — include 4-8 techniques that span the attack chain (initial access → impact). Use real technique IDs. Leave empty rather than fabricate.

**Tool-sourced injects** — name a specific detection or alert only when it is confirmed by user-provided context or an authorized source; never fabricate a rule name.

### 4. Validate

Before writing, run both checks:

- **Stack grounding** — ensure named tools and workflows match the stack the user described. Mark unconfirmed assumptions, or keep the language generic when the stack is unknown. Do not substitute a familiar product for the user's product or require a canonical inventory. Confirm each named detection rule against a source the user provided or authorized.
- **Inject temporal consistency** — each inject's `expected_actions` may only respond to information available up to and including that inject. Walk the injects in order and reject any expected action that references, presupposes, or foreshadows a *later* inject — meta-phrases like "in the next inject" and actions that hinge on a fact the scenario hasn't revealed yet. See `references/scenario-schema.md` → `expected_actions`.

### 5. Write the JSON file

Save completed scenarios as `scenarios_output/<scenario_id>.json` relative to this skill's directory (`skills/ttx-scenario-generator/scenarios_output/` in this repository), regardless of the user's current working directory. The `scenario_id` already begins with `ttx-`. Create the directory if it does not exist. Use a different path only when the user explicitly requests one.

`scenario_id` format: `ttx-YYYY-MM-DD-NN` where NN is a 2-digit sequence (start at 01; if a file with that ID exists in the output dir, increment).

After writing, show the user:

1. The output path.
2. A summary card: title, type, framing (internal vs vendor-responsibility), module count, total duration, technologies, threat actor, NIST CSF coverage.
3. The first two injects so they can sanity-check the flavor.
4. Counts: number of injects, number of inline discussion questions, number of appendix questions.

Don't dump the entire JSON to chat — it's long. Offer to read sections back on request.

## Example invocations

**Generic**:
> "Generate a TTX scenario."

→ Present menu, defaults for difficulty/duration, generate.

**Specific**:
> "Make me a 90-minute high-difficulty ransomware scenario. Our email platform is ExampleMail, our endpoint tool is ExampleEDR, and our identity provider is ExampleID."

→ Use the supplied stack names and capabilities. Ask about any critical gaps, such as alert routing or available logs, before adding detailed telemetry.

**Mirroring real patterns**:
> "Build a tabletop based on the kind of cloud incidents we've actually been seeing."

→ Ask which incident records or approved sources can be used. Learn only anonymized patterns; never copy ticket content. Build a fictional scenario that uses the same shape.

**Supply-chain / vendor-responsibility**:
> "I want a vendor-responsibility scenario — our build pipeline gets compromised, like SolarWinds."

→ Use `framing = vendor-responsibility`. Pull product-security-relevant discussion questions.

## What this skill does NOT do

- It does not run the exercise — it produces the JSON.
- It does not replay real incidents verbatim. Patterns yes, specifics no.
- It does not assume the audience is non-technical. Language can be precise.
- It does not include solutions in participant-facing fields — those go in `appendices.facilitator_notes`.
- It does not represent the scenario as a real event. The JSON must mark itself fictional in `metadata.fictional_disclaimer`.

## Reference files

- `references/security-stack.md` — questions and validation guidance for grounding tool names in the user's described stack.
- `references/scenario-schema.md` — full JSON schema, field by field, with examples.
- `references/question-bank.md` — categorized library of generic CISA-derived discussion questions. Adapt it to the user's organization and stack.
- `references/mcp-grounding.md` — safe, targeted use of connected sources when the user authorizes them.
- `references/detection-grounding.md` — how to verify specific detection references against user-provided or authorized sources.
