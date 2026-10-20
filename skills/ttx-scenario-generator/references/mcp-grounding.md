# Grounding TTX Scenarios in Approved Sources

Use connected apps, repositories, or documents only when the user has supplied or authorized the source and it is available in the current session. Do not assume access to a particular company's systems or search broadly for internal material.

## Choose targeted sources

Use the smallest number of relevant searches that can answer a concrete scenario question. Depending on what the user authorizes, sources may include:

- Incident response plans and playbooks for roles, escalation criteria, and notification steps
- Anonymized incident records for recurring patterns, without copying case details
- Architecture or inventory documents to confirm system relationships and tool names
- Detection repositories or alert documentation to verify exact rule names and severity
- Public threat research to validate actor behavior, techniques, and indicator types

If source authorization is unclear, ask before accessing internal records. If no source is available, continue with the user's description and clearly mark assumptions.

## Protect source material

- Use source material to understand patterns, capabilities, and process. Do not copy incident narratives or operational details into the scenario.
- Never include real ticket identifiers, employee or customer names, credentials, internal hostnames, private IP ranges, real IOCs, or sensitive query results.
- Paraphrase and anonymize relevant lessons. Keep the scenario fictional and mark it in `metadata.fictional_disclaimer`.
- Fabricate realistic-looking indicators for exercise use; do not reuse real indicators from threat research or internal telemetry.
- Record source types in `metadata.grounding_sources_used` without exposing sensitive content or unnecessary internal identifiers.

## Record grounding

Use a short description of the source and how it informed the scenario. For example:

```json
"grounding_sources_used": [
  "Incident response plan: escalation roles (paraphrased)",
  "Anonymized incident records: cloud credential exposure pattern",
  "Public threat research: attacker technique sequence"
]
```

If no external grounding was performed, use an empty list. Do not imply that a source was consulted when it was not.
