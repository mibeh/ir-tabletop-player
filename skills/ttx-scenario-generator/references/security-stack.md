# Grounding a Scenario in the User's Security Stack

Use this guide to gather enough environment detail for a realistic exercise without assuming a particular organization's products, configurations, or procedures.

## Ask for relevant context

When the user has not already provided it, ask them to describe the tools and systems relevant to the scenario. A concise prompt can request:

- Endpoint detection and response
- Identity providers and privileged access management
- Cloud platforms and cloud security monitoring
- Email and collaboration services
- Security information and event management, log sources, and alert routing
- Security orchestration and incident or ticket management
- Backups, critical business services, and recovery ownership
- Relevant teams, escalation paths, and response playbooks

Ask only for the areas needed by the scenario. The user can provide product names, internal names, generic capability descriptions, or say they prefer not to share details.

## Use supplied details carefully

- Preserve product and system names as the user supplied them. Do not replace them with familiar alternatives.
- Distinguish confirmed facts from assumptions. Do not invent configurations, integrations, coverage, response times, teams, playbooks, or alert names.
- If a capability is unknown, ask a focused follow-up or describe the gap as a decision for participants.
- When the user prefers not to disclose tools, use role descriptions such as "endpoint detection tool" or "identity provider" without guessing a vendor.
- Use fictional but plausible identifiers for hosts, accounts, IP addresses, domains, tickets, and cloud resources. Mark the scenario as fictional in metadata.
- Include only stack details needed to support the scenario's attack chain and discussion objectives.

## Validate before finalizing

Review `technologies_involved`, `trigger_source`, inject narratives, indicators, expected actions, success criteria, and facilitator notes. Check that:

1. Each named product and system comes from user-provided context or a source the user authorized.
2. Capabilities described for each tool are supported by the provided context. Otherwise, rephrase the behavior as an assumption or participant decision.
3. No scenario content exposes real credentials, personal data, customer data, incident records, or other sensitive source material.
4. Real detection names, severities, and alert behavior are included only when verified against an approved source.

If no stack details or sources are available, keep tool references generic and record that grounding was not performed in `metadata.grounding_sources_used`.
