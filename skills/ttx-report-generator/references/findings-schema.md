# Findings JSON Schema

`render_aar.py` consumes a single JSON object with the keys below. Every field
is optional at render time (the renderer substitutes sensible defaults), but a
good report fills them all. Author this object yourself from your analysis of
the three inputs, then pass it to the renderer.

## Top-level shape

```jsonc
{
  "exercise_overview": {
    "name": "Operation Paper Trail — Finance BEC via M365 Credential Phish",
    "dates": "2026-05-29",
    "scope": "An interactive, discussion-based TTX of ~2.5 hours for an internal organization.",
    "mission_areas": ["Protection", "Response", "Recovery"],
    "core_capabilities": ["Cybersecurity", "Operational Coordination"],
    "objectives": ["Exercise the BEC playbook end-to-end.", "..."],
    "threat_or_hazard": "Cyber Incident — Business Email Compromise",
    "scenario_description": "An AiTM phishing attack against Finance.",
    "modules": [{ "number": 1, "title": "Detection" }],
    "sponsor": "IR Team",
    "participating_organizations": "SOC, IR, Finance, IT Identity, Legal.",
    "points_of_contact": "Facilitator: <name>, <email>",
    "caveat": "Fictional Training Exercise — Not a Real Incident"
  },
  "executive_summary": "A narrative (blank lines separate paragraphs) that frames the exercise objectives and summarizes the most important strengths and areas for improvement.",
  "objective_capability_alignment": [
    { "objective": "Exercise the BEC playbook end-to-end.",
      "core_capabilities": ["Cybersecurity"] }
  ],
  "objective_analyses": [
    {
      "number": 1,
      "objective": "Exercise the BEC playbook end-to-end.",
      "core_capabilities": ["Cybersecurity"],
      "strengths": ["Complete-sentence strength grounded in the transcript."],
      "areas_for_improvement": [
        {
          "observation": "Clear statement of the gap.",
          "priority": "High",
          "references": ["BEC Playbook v3"],
          "analysis": "The most detailed part: behavior, what was discussed, consequences.",
          "recommendation": "How to close the gap (not a corrective action)."
        }
      ]
    }
  ],
  "improvement_plan": [
    {
      "exercise_objective": "Exercise the BEC playbook end-to-end.",
      "core_capability": "Cybersecurity",
      "issue": "No session-revocation step in the playbook.",
      "priority": "High",
      "corrective_actions": ["Update the BEC playbook to require session revocation."],
      "capability_element": "Planning",
      "responsible_organization": "IR",
      "poc": "<name>",
      "start_date": "2026-06-15",
      "completion_date": "2026-07-15"
    }
  ],
  "participants": [
    { "name": "Alex Chen", "position": "SOC Analyst",
      "exercise_role": "Participant", "department": "SOC" }
  ]
}
```

The `participants` objects mirror the platform's exercise roster: `name`,
`position`, `exercise_role` (`Facilitator`, `Participant`, or `Observer`), and
`department`. Copy them straight from the completion package's `participants`.

## Defaults the renderer applies

- `sponsor` → "IR Team"
- `caveat` → "Fictional Training Exercise — Not a Real Incident"
- Empty `executive_summary` → "No executive summary was provided for this exercise."
- Empty `strengths` → "No major strengths recorded for this objective."
- Empty `areas_for_improvement` → "No areas for improvement recorded for this objective."
- Empty `references` → "Not Applicable"
- Empty `priority` → "Not Specified"

## Priority

`priority` (on each `areas_for_improvement` entry and each `improvement_plan`
row) must be one of: `Critical`, `High`, `Medium`, `Low`. It renders as a line
in the objective analysis and as the Priority column in Appendix A.

## Capability Elements

`capability_element` must be one of: `Planning`, `Organization`, `Equipment`,
`Training`, `Exercise`.

## Core Capabilities (cyber-relevant subset)

Cybersecurity; Operational Coordination; Operational Communications; Public
Information and Warning; Situational Assessment; Forensics and Attribution;
Access Control and Identity Verification; Intelligence and Information Sharing;
Infrastructure Systems.
