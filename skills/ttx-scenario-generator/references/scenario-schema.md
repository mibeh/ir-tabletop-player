# TTX Scenario JSON Schema

This schema follows the structure of CISA's Tabletop Exercise Package (CTEP) format. Adapt examples and tool references to the user's organization and confirmed security stack.

## Top-level structure

```json
{
  "scenario_id": "ttx-2026-05-26-01",
  "metadata": { ... },
  "exercise_overview": { ... },
  "exercise_guidelines": [ ... ],
  "scenario_details": { ... },
  "modules": [ ... ],
  "hotwash": { ... },
  "appendices": { ... },
  "success_criteria": [ ... ]
}
```

---

## `scenario_id` (required)

Format: `ttx-YYYY-MM-DD-NN`. The NN is a 2-digit sequence number scoped to the day. Start at `01`; if the target output directory already contains a scenario with that ID, increment.

## `metadata`

```json
{
  "generated_at": "2026-05-26T16:30:00Z",
  "fictional_disclaimer": "This scenario is a training exercise. Names, indicators, customer references, and incident details are fabricated. Any resemblance to real incidents is illustrative only.",
  "grounding_sources_used": [
    "Incident response plan: escalation roles (paraphrased)",
    "Public threat research: attacker technique sequence",
    "Anonymized incident records: cloud credential exposure pattern"
  ],
  "framing": "internal"
}
```

`framing` is `"internal"` or `"vendor-responsibility"` (see SKILL.md for definitions). Default to `internal` unless the user requests another perspective.


## `exercise_overview`

```json
{
  "name": "Operation Glasshouse — Cloud Credential Exposure Tabletop",
  "activity_timeline": [
    { "duration_minutes": 20, "activity": "Threat Briefing and Opening Remarks" },
    { "duration_minutes": 60, "activity": "Module 1" },
    { "duration_minutes": 20, "activity": "Break" },
    { "duration_minutes": 60, "activity": "Module 2" },
    { "duration_minutes": 20, "activity": "Hotwash" }
  ],
  "purpose": "Examine the organization's incident response capabilities after a significant cloud credential compromise.",
  "nist_csf_functions": ["Govern", "Identify", "Protect", "Detect", "Respond", "Recover"],
  "objectives": [
    "Exercise the response playbook for compromised cloud credentials.",
    "Practice triaging a cloud security alert and investigating relevant audit logs.",
    "Identify gaps between cloud monitoring and available audit data.",
    "Evaluate cross-team coordination between IR, GRC, and Legal for cloud incidents."
  ],
  "threat_or_hazard": "Cyber Incident",
  "scenario_summary": "A cloud access key associated with a production identity is exposed in a public source repository. A security alert prompts the team to triage, contain, and determine scope."
}
```

## `exercise_guidelines`

```json
[
  "This exercise is held in an open, no-fault environment. Varying viewpoints are expected.",
  "Respond to the scenario using your knowledge of existing plans, capabilities, training, and experience.",
  "Decisions are not precedent-setting and do not reflect the organization's final position on any issue.",
  "There is no hidden agenda and no trick questions.",
  "Assumptions and artificialities are necessary to complete play within the given time. Do not let these factors negatively impact your participation."
]
```

## `scenario_details`

Internal-facing scenario metadata that the facilitator uses to plan and that informs the narrative across modules.

```json
{
  "title": "Operation Glasshouse — Cloud Credential Exposure",
  "scenario_type": "cloud_compromise",
  "difficulty": "medium",
  "target_audience": ["IR Team", "SOC", "Security Leadership", "GRC"],
  "background": "The organization's production cloud account hosts batch analytics workloads. A migration of infrastructure state from a developer-owned source repository to a restricted workspace is partially complete. The data team is small, and its on-call rotation is informal.",
  "threat_actor": {
    "name": "SCATTERED_SPIDER (fictional analogue)",
    "type": "criminal",
    "motivation": "Financial — credential resale, ransomware staging, extortion",
    "sophistication": "high",
    "ttps_summary": "Social engineering of help desk, MFA fatigue, cloud credential harvesting, lateral movement via legitimate admin tools, data exfiltration over sanctioned channels."
  },
  "mitre_attack": {
    "tactics": ["Initial Access", "Credential Access", "Discovery", "Collection", "Exfiltration"],
    "techniques": [
      { "id": "T1552.001", "name": "Credentials In Files" },
      { "id": "T1078.004", "name": "Valid Accounts: Cloud Accounts" },
      { "id": "T1580", "name": "Cloud Infrastructure Discovery" },
      { "id": "T1530", "name": "Data from Cloud Storage" },
      { "id": "T1567.002", "name": "Exfiltration to Cloud Storage" }
    ]
  },
  "technologies_involved": [
    { "name": "Cloud security monitoring", "role": "Initial alert source — flagged exposed cloud credential" },
    { "name": "Cloud provider", "role": "Environment under attack" },
    { "name": "Cloud audit logs", "role": "Activity queried during triage" },
    { "name": "Endpoint detection and response", "role": "Endpoint telemetry for the developer machine where the key was created" },
    { "name": "Privileged credential store", "role": "May contain other credentials at risk" },
    { "name": "Identity provider", "role": "Sign-in and identity audit context" },
    { "name": "Incident tracking system", "role": "Incident coordination and tracking" }
  ]
}
```

`scenario_type` is one of (or hyphenated combination):

`ransomware`, `insider_threat`, `supply_chain`, `account_takeover`, `business_email_compromise`, `cloud_compromise`, `credential_theft`, `data_exfiltration`, `privileged_access_abuse`, `apt_espionage`, `detection_bypass`, `third_party_breach`, `denial_of_service`, `vendor_responsibility`, `zero_day_exploit`, `phishing_campaign`, `mfa_bypass`, `data_destruction`, `extortion`, `iam_misconfiguration`.

`difficulty`:

- **low** — single attack vector, clear indicators, mostly tests basic playbook execution.
- **medium** — 2-3 phases of attack, some ambiguity in indicators, requires cross-team coordination.
- **high** — multi-stage, deliberate evasion, conflicting/incomplete signals, requires judgment calls under uncertainty.

## `modules`

Array of one or two modules. Each module is a phase of the exercise.

```json
[
  {
    "number": 1,
    "title": "Initial Detection and Scoping",
    "duration_minutes": 60,
    "summary": "A cloud security finding surfaces an exposed access key. The team must triage, determine scope of access, and decide on initial containment.",
    "injects": [
      {
        "sequence": 1,
        "day_or_time": "Day 1 — 14:02 UTC",
        "trigger_source": "Cloud security alert",
        "trigger_condition": "Start of exercise",
        "title": "Critical cloud security alert: access key exposed in public source repository",
        "narrative": "A cloud security alert reports that an access key associated with a production identity appears in a public source repository. The key was last used 47 minutes ago from an unfamiliar source address (203.0.113.66).",
        "indicators": [
          "Cloud access key ID: 4H7K2M9Q6B3D8R5T1W0X",
          "Source IP of recent usage: 203.0.113.66 (unfamiliar source address)",
          "Repository visibility: public"
        ],
        "expected_actions": [
          "Confirm the finding in the cloud security monitoring system",
          "Review available cloud audit logs for the identity over the last 24 hours",
          "Open an incident record and notify the response lead"
        ],
        "discussion_questions": [
          {
            "category": "Incident Identification",
            "nist_csf_function": "Detect",
            "question": "What is the first action the on-call analyst should take after acknowledging the cloud security finding?",
            "follow_ups": [
              "What is the expected response time for triaging a critical finding?",
              "Who has the authority to escalate this to a declared incident?"
            ]
          },
          {
            "category": "Incident Response",
            "nist_csf_function": "Respond",
            "question": "What additional log sources would you query to confirm the scope of access?",
            "follow_ups": [
              "How do you correlate cloud activity with endpoint telemetry from the developer's machine?",
              "How long is cloud audit data retained, and is that long enough for this investigation?"
            ]
          }
        ]
      }
    ]
  }
]
```

**Inject fields**:

- `sequence` — 1-based within the module.
- `day_or_time` — CISA-style timestamp (e.g., `Day 1`, `Day 31 — Morning`, `Day 50`). Helps facilitators pace the exercise.
- `trigger_source` — which user-confirmed tool or process surfaces this information. Use the user's terminology; otherwise use a generic capability label such as `Endpoint detection alert`, `User report`, `Vendor notification`, or `Facilitator narration`. Verify any named detection rule against a source the user provided or authorized; see `references/detection-grounding.md`.
- `trigger_condition` — `"time"`, `"start of exercise"`, `"when team asks about X"`, etc. Tells the facilitator when to deliver this inject.
- `title` — short label.
- `narrative` — 2-5 sentences of what the facilitator presents to participants.
- `indicators` — fictional IOCs or data points that come with the inject. Make each value plausible for its type and never embed `FICTIONAL`/`EXAMPLE`/`XXXX`/`<…>` placeholder tokens (see **Make indicators look real** below). Include a specific detection name or severity only when verified against an approved source; surrounding exercise indicators stay fabricated.
- `expected_actions` — facilitator-facing (NOT for participants). What a competent team *would* do in response to the information available **at this point**: this inject's `narrative` and `indicators` plus everything disclosed in earlier injects. Never reference, presuppose, or foreshadow anything a *later* inject introduces — no meta-phrases like "feed this into the next inject," and no action that only makes sense once a not-yet-revealed fact is known (e.g., don't say "restore audit logging" in an inject that runs *before* logging is disabled). Forward-looking IR steps grounded in what's known now are fine — "plan to revoke the service principal and refresh tokens" after a consent grant is good practice, not a spoiler.
- `discussion_questions` — 2-5 questions tied to this inject.

**Tool-sourced inject** — name a real detection only when verified (rule name and severity verified; IOCs fabricated):

```json
{
  "sequence": 2,
  "day_or_time": "Day 1 — 14:31 UTC",
  "trigger_source": "Endpoint detection alert",
  "trigger_condition": "time",
  "title": "Alert: cloud audit logging disabled in production",
  "narrative": "A verified detection reports that audit logging was disabled in the production environment, 29 minutes after the access-key exposure finding.",
  "indicators": [
    "Verified detection: cloud audit logging disabled",
    "Event: audit logging configuration changed",
    "Source IP: 203.0.113.66 (unfamiliar source address)"
  ],
  "expected_actions": [
    "Treat the logging change as an escalation and raise incident severity in the incident tracking system",
    "Restore audit logging and check for other defense-evasion activity from the same identity"
  ]
}
```

**Make indicators look real (no placeholder tokens)**

The scenario is marked fictional once — in `metadata.fictional_disclaimer`. Do **not** repeat that marking inside individual values. Never embed `FICTIONAL`, `EXAMPLE`, `SAMPLE`, `PLACEHOLDER`, `XXXX`, an angle-bracket `<…>` slot, a `.x.x` octet mask, or a trailing `(fictional)` / `(fake)` note inside an ID, hash, domain, username, ARN, key, or rule name — those read as fake and break immersion. Fabricate a value in the artifact's real format instead. Safety comes from the *format*, not a label: fabricated IPv4 addresses use the RFC 5737 documentation ranges, and external/hostile domains and URLs are defanged with `[.]`.

| Artifact | Real format | Fabricated example |
|---|---|---|
| Cloud credential ID | Use the provider's documented format when the user supplies it | A realistic fabricated identifier for the named provider |
| Cloud account or tenant ID | Use the provider's documented format when known | A realistic fabricated identifier for the named provider |
| Cloud resource identifier | Use the provider's documented format when known | A realistic fabricated identifier for the named provider |
| File hash | 64 hex chars (SHA-256) | `e7b91c4d8a2f6b03d1c95e0a7f48b2691d3c6a04f1e8927b5c0a3d6f8e1b4c72` |
| App / client ID, request or correlation GUID | `8-4-4-4-12` hex | `a7f3c9e2-4b1d-4e2a-9c6f-2d8e5a1b3c4f` |
| CVE ID | `CVE-YYYY-NNNNN` | `CVE-2026-31847` |
| IPv4 (fabricated) | RFC 5737 ranges `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` | `203.0.113.66` |
| Internal user / email | `first.last@example.org` | `maria.delgado@example.org` |
| External / hostile domain | plausible name, **defanged** with `[.]` | `docuflow-sync[.]app` |
| Email message ID | `<token@domain>` | `<a3f1c9e24b1d@mail.protection.outlook.com>` |
| Commit SHA | 7–40 hex | `9f3c1ab2d7e4` |
| Detection rule name | Verified against an authorized source | Use the exact confirmed name (see `references/detection-grounding.md`) |

You may annotate an indicator's *role* in plain prose — `203.0.113.66 (known TOR exit-node range)`, `docuflow-sync[.]app (lookalike of the supplier domain)` — since that's realistic analyst context. Annotate what the indicator *is*, never that it's invented.

**Discussion question fields**:

- `category` — one of: `Cyber Resilience`, `Accounts & Privileges`, `Incident Identification`, `Incident Response`, `Recovery`, `Training & Exercises`, `Senior Leaders`, `Public Information`, `Legal`, `Product Security`, `Communications`, `Detection`, `Triage`, `Containment`, `Eradication`, `Post-incident`.
- `nist_csf_function` — one of: `Govern`, `Identify`, `Protect`, `Detect`, `Respond`, `Recover`.
- `question` — open-ended.
- `follow_ups` — array of drill-down sub-questions (CISA's standard pattern).

## `hotwash`

```json
{
  "duration_minutes": 20,
  "purpose": "Identify strengths and areas for improvement immediately following exercise conduct.",
  "guiding_questions": [
    "What worked well in the team's response?",
    "Where did the playbook fall short or feel ambiguous?",
    "What detection or prevention change would have caught this 30 minutes earlier?",
    "What cross-team coordination was missing or unclear?",
    "What is the single highest-priority follow-up action from this exercise?"
  ]
}
```

## `appendices`

```json
{
  "additional_discussion_questions": {
    "Cyber Resilience": [
      { "nist_csf_function": "Govern", "question": "...", "follow_ups": [...] }
    ],
    "Accounts & Privileges": [...],
    "Incident Identification": [...],
    "Incident Response": [...],
    "Recovery": [...],
    "Training & Exercises": [...],
    "Senior Leaders": [...],
    "Public Information": [...],
    "Legal": [...],
    "Product Security": [...]
  },
  "facilitator_notes": {
    "key_decision_points": [
      "After inject 2: team must decide whether to engage GRC. Pause here if they don't."
    ],
    "common_pitfalls": [
      "Teams often skip checking for established sessions and stop at key rotation.",
      "Cross-region enumeration is easy to miss if only querying us-east-1 logs."
    ],
    "hints_to_provide_if_stuck": [
      "If the team is not reviewing object-access logs, mention that the source address also appears in storage-read events.",
      "If the team isn't considering session tokens, ask: 'What does the adversary still have after you rotate the key?'"
    ],
    "wrap_up_themes": [
      "Cloud credential exposure detection latency.",
      "When 'rotate and move on' is insufficient."
    ]
  },
  "references": {
    "internal_playbooks": ["Incident response playbook: cloud access key compromise (paraphrased reference)"],
    "mitre_attack_url": "https://attack.mitre.org/",
    "external_threat_intel": ["Public threat research: relevant attacker profile"],
    "cisa_resources": [
      "CISA Cross-sector Cybersecurity Performance Goals — https://www.cisa.gov/cross-sector-cybersecurity-performance-goals",
      "NIST Cybersecurity Framework — https://www.nist.gov/cyberframework"
    ]
  }
}
```

## `success_criteria`

How the facilitator judges whether the exercise met its objectives. Specific and observable.

```json
[
  "Team identifies that key rotation alone is insufficient and explicitly considers AssumeRole session revocation.",
  "Team articulates a clear decision tree for whether to engage GRC and on what timeline.",
  "Team queries at least three log sources before declaring scope.",
  "Team identifies at least one detection gap and assigns a follow-up owner."
]
```
