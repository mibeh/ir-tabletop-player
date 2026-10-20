# Appendix Discussion Question Bank

A categorized library of discussion questions for the scenario's `appendices.additional_discussion_questions` block. Derived from CISA's CTEP Appendix A question banks (TLP:CLEAR). Adapt questions to the user's organization and confirmed security stack.

**How to use**: When composing a scenario, pull ~20-40 questions across these categories. Pick the ones most relevant to the scenario type and audience. Each question carries an inferred NIST CSF function — keep it; it's how facilitators can spot framework-coverage gaps. Add or modify follow-ups based on the specific scenario.

The first ten section headers below (`Cyber Resilience` through `Product Security`) map 1:1 to values in the schema's `category` enum (see `scenario-schema.md`); use them directly as keys in `appendices.additional_discussion_questions`.

The last two sections (`Supply Chain & Third-Party`, `Cloud-Specific`) are **scenario-type banks**, not categories. The questions inside them cross-cut multiple categories. When inserting one of those questions into a scenario, assign it to whichever enum category fits best (e.g., a vendor-contract question → `Legal`; a C-SCRM-inventory question → `Cyber Resilience`; a cloud-credential-rotation question → `Incident Response`).

Format every entry as:

```json
{
  "nist_csf_function": "Govern|Identify|Protect|Detect|Respond|Recover",
  "question": "...",
  "follow_ups": ["...", "..."]
}
```

---

## Cyber Resilience

```json
[
  {
    "nist_csf_function": "Govern",
    "question": "What are the organization's cybersecurity objectives, and how do they align with business objectives?",
    "follow_ups": [
      "How are these objectives reviewed and updated?",
      "Who owns each objective?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "Describe the review process for the corporate Cyber Incident Response Plan (CIRP).",
    "follow_ups": [
      "How often is the CIRP reviewed and by whom?",
      "How is the CIRP integrated with other emergency/incident response plans?",
      "How are updates communicated to the broader organization?"
    ]
  },
  {
    "nist_csf_function": "Identify",
    "question": "What information assets and systems are most critical to the organization's continued operations, and how is that prioritization maintained?",
    "follow_ups": [
      "What is the source of truth for the asset inventory?",
      "How often is the criticality classification reviewed?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "How is defense-in-depth implemented across the corporate environment, and where are the known thinnest layers?",
    "follow_ups": [
      "Are there areas where defense-in-depth practices could be strengthened?",
      "How do you validate that compensating controls actually compensate?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "How often are corporate cybersecurity plans, policies, and procedures externally reviewed or audited?",
    "follow_ups": [
      "What were the most recent results and action items?",
      "What residual risks remain unmitigated and accepted by whom?"
    ]
  }
]
```

## Accounts & Privileges

```json
[
  {
    "nist_csf_function": "Protect",
    "question": "What are the organization's policies and procedures for IT account lifecycle management?",
    "follow_ups": [
      "What are the protocols for provisioning, modifying, disabling, and removing accounts?",
      "How quickly are accounts disabled when an employee leaves?",
      "How are dormant accounts identified and removed?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "How are privileged credentials managed, and how does that process interact with the organization's privileged credential store?",
    "follow_ups": [
      "Which credentials are managed in the privileged credential store, and which are managed elsewhere?",
      "How are break-glass accounts protected and audited?",
      "How are service account credentials rotated?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "Describe the organization's Zero Trust Architecture (ZTA) approach and how it applies to the scenario.",
    "follow_ups": [
      "Which systems still rely on implicit trust based on network location?",
      "How are workload identities authenticated in cloud environments?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "How could the organization's identity monitoring tools surface anomalous behavior in this scenario?",
    "follow_ups": [
      "What identity signals are *not* being collected today?",
      "How are identity findings routed into the incident tracking process?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "What is the off-boarding process for employees with elevated privileges?",
    "follow_ups": [
      "Is this coordinated with IT, HR, and Legal?",
      "What additional actions are taken if the termination is contentious?",
      "How is access to privileged credential stores, remote access tools, and administrator consoles revoked?"
    ]
  }
]
```

## Incident Identification

```json
[
  {
    "nist_csf_function": "Detect",
    "question": "How are cyber incidents reported within the organization, both through tools and out-of-band channels?",
    "follow_ups": [
      "What triggers a regulatory or contractual reporting obligation?",
      "What training do employees receive on incident reporting?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "Which of the organization's security tools and data sources can detect activity in this scenario?",
    "follow_ups": [
      "Where do detection blind spots exist between these tools?",
      "How are findings correlated across the tools?",
      "Which tool is authoritative when two disagree?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "What escalation criteria are defined in the CIRP, and how do they apply to the alert presented in this scenario?",
    "follow_ups": [
      "Who is responsible and what actions would they take?",
      "Who is notified internally and externally according to the plan?",
      "When would leadership and the CISO be notified?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "How would the team determine whether unauthorized manipulation of data has occurred?",
    "follow_ups": [
      "What integrity-monitoring capabilities are in place?",
      "How are baselines maintained?"
    ]
  }
]
```

## Incident Response

```json
[
  {
    "nist_csf_function": "Respond",
    "question": "Describe the IR team's processes for collecting evidence and maintaining chain of custody during this incident.",
    "follow_ups": [
      "What evidence collection automation exists (for example, endpoint response actions or cloud snapshots)?",
      "How is evidence stored, and for how long?",
      "Who has access to evidence and how is that controlled?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "At what point in the scenario would the organization contact law enforcement?",
    "follow_ups": [
      "Who has the authority to make that call?",
      "How would a law enforcement investigation impact containment and recovery efforts?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How are third-party vendors involved in the incident response?",
    "follow_ups": [
      "How is this documented in the CIRP?",
      "What does the SLA include regarding incident response activity?",
      "How is a vendor breach detected if the vendor does not notify?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "What are the processes for contacting critical personnel outside core hours?",
    "follow_ups": [
      "How do you proceed if critical personnel are unreachable?",
      "What are the backup decision-makers for each role?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How does the organization coordinate response across incident response, security operations, engineering, governance, risk and compliance, and Legal?",
    "follow_ups": [
      "Who owns the incident at each phase?",
      "Where is the canonical timeline maintained?"
    ]
  }
]
```

## Recovery

```json
[
  {
    "nist_csf_function": "Recover",
    "question": "When and how does the organization determine that the incident is resolved?",
    "follow_ups": [
      "Who makes this decision?",
      "What criteria must be met before declaring closure?"
    ]
  },
  {
    "nist_csf_function": "Recover",
    "question": "What post-incident activities would the organization conduct following this scenario?",
    "follow_ups": [
      "Who facilitates the post-mortem, and who attends?",
      "How are lessons learned tracked through to completion?"
    ]
  },
  {
    "nist_csf_function": "Recover",
    "question": "What actions would the team take if IR/SOC cannot confirm the integrity of affected systems or data?",
    "follow_ups": [
      "What is the threshold for full rebuild vs. selective remediation?",
      "How long and costly is the process to completely rebuild critical systems?"
    ]
  },
  {
    "nist_csf_function": "Recover",
    "question": "Describe the organization's policies and procedures for verifying backup integrity before restoration.",
    "follow_ups": [
      "How frequently are backup restorations tested?",
      "How is the integrity of backup data validated before restoration?",
      "What is the retention horizon, and is it sufficient for this scenario?"
    ]
  }
]
```

## Training & Exercises

```json
[
  {
    "nist_csf_function": "Govern",
    "question": "What training does the cybersecurity incident response team undergo to detect, analyze, and report malicious activity?",
    "follow_ups": [
      "What additional training is required for staff with system-admin privileges?",
      "How often do team members rotate through the on-call queue?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "How often does the organization exercise its incident response plan, and who participates?",
    "follow_ups": [
      "How often do senior staff and leadership participate?",
      "What external partners are involved in exercises?",
      "How are exercise findings tracked to closure?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "How are findings from exercises like this one fed back into the CIRP, runbooks, and team training?",
    "follow_ups": [
      "Who owns tracking exercise-derived action items to closure?",
      "What is the SLA for closing exercise findings?",
      "How do you avoid re-discovering the same gap in successive exercises?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "What ongoing technical training (purple team, red team debriefs, threat-hunting practice) does the IR/SOC team receive beyond CIRP exercises?",
    "follow_ups": [
      "How is training time protected against on-call and project load?",
      "What is the budget and cadence for external training (SANS, conferences)?"
    ]
  }
]
```

## Senior Leaders

```json
[
  {
    "nist_csf_function": "Govern",
    "question": "As a leader, what cyber resilience goals have you set, and how do they align with organizational objectives?",
    "follow_ups": [
      "How is progress against those goals measured and reported?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "At what point in the scenario would you activate the broader crisis-management team?",
    "follow_ups": [
      "What information do you need to support that decision?",
      "Who else is in the room when that decision is made?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "What information do you need to brief the board, the CEO, or external stakeholders during this scenario?",
    "follow_ups": [
      "How quickly can the team produce that information?",
      "What is the cadence of executive updates during an active incident?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How do you balance speed of decision-making against the need for legal review and confirmed information during this scenario?",
    "follow_ups": [
      "Where in the response do you accept information that is not yet confirmed?",
      "How is a decision reversed when new information contradicts it?",
      "What is the threshold for invoking outside counsel or external IR firms?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "What is your decision authority and budget for emergency third-party services (forensics, ransom negotiation, PR) during this scenario?",
    "follow_ups": [
      "What contracts and retainers are already in place?",
      "Who can authorize spend outside normal approval workflows?"
    ]
  }
]
```

## Public Information

```json
[
  {
    "nist_csf_function": "Respond",
    "question": "What incident-related information would be shared internally with employees and leadership?",
    "follow_ups": [
      "What is the cadence of internal updates?",
      "Who drafts and approves internal communications?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "What incident-related information would be shared externally with customers, partners, and the public?",
    "follow_ups": [
      "Who owns customer communications during an active incident?",
      "How are customer-facing messages reviewed by Legal and Communications?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How does the organization handle media inquiries during this scenario?",
    "follow_ups": [
      "Who is the designated spokesperson?",
      "What training do employees receive on media contact?"
    ]
  },
  {
    "nist_csf_function": "Recover",
    "question": "How would the organization work to rebuild customer trust following this incident?",
    "follow_ups": [
      "What public artifacts (post-mortem, security advisory) would be published?",
      "What changes would be made to product or process to demonstrate improvement?"
    ]
  }
]
```

## Legal

```json
[
  {
    "nist_csf_function": "Govern",
    "question": "What is the role of Legal during this scenario, and when are they engaged?",
    "follow_ups": [
      "What triggers privileged engagement?",
      "What documents would Legal draft or review?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "What legal and regulatory notifications are required based on the scenario, and on what timelines?",
    "follow_ups": [
      "Who is responsible for making the notifications?",
      "How are notification timelines tracked?",
      "Which jurisdictions apply (GDPR, US state laws, sector-specific)?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "What is the organization's potential legal liability if a customer is affected by this incident?",
    "follow_ups": [
      "How are contractual SLAs interpreted in this context?",
      "What insurance coverage applies?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How does Legal coordinate with outside counsel during this scenario, and at what point are they engaged?",
    "follow_ups": [
      "What information is shared in writing vs. verbally to preserve privilege?",
      "How are forensics vendors retained — directly or through outside counsel?",
      "What is the standing retainer arrangement, and is it sufficient for this scenario's complexity?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How are evidence preservation and litigation hold triggered during this scenario?",
    "follow_ups": [
      "Who issues the litigation hold notice and to whom?",
      "How does the hold interact with normal retention and deletion policies?",
      "How is hold compliance verified?"
    ]
  }
]
```

## Product Security

```json
[
  {
    "nist_csf_function": "Govern",
    "question": "What is the role of Product Security during this incident, and how do they coordinate with Corporate IR?",
    "follow_ups": [
      "Where do customer-facing vulnerabilities trigger a different response track than internal incidents?",
      "Who decides whether a finding becomes a customer-facing security advisory?",
      "How is Product Security's involvement documented in the incident and vulnerability tracking processes?"
    ]
  },
  {
    "nist_csf_function": "Identify",
    "question": "What is the organization's coordinated vulnerability disclosure (CVD) policy, and how does it apply if this scenario originated as an external researcher report?",
    "follow_ups": [
      "What is the published intake channel and acknowledgement SLA?",
      "How is researcher contact handled if the vulnerability is being actively exploited in the wild?",
      "When and how is an embargo coordinated with affected customers and partners?",
      "How is researcher credit and bounty handled if applicable?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "What SDLC security controls should have caught this issue earlier, and which were bypassed or absent?",
    "follow_ups": [
      "Are threat models maintained for the component involved, and when were they last updated?",
      "What static analysis, dynamic analysis, fuzzing, and dependency scanning runs in the pipeline?",
      "How are pre-release security findings tracked to closure, and what is the SLA?",
      "What was the test coverage on the affected code path?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "How is the integrity of the build and release pipeline protected against tampering?",
    "follow_ups": [
      "What signing, provenance (SLSA), and SBOM controls are in place?",
      "How are build environments isolated and access-controlled?",
      "How would you detect a malicious modification introduced into a release artifact?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "How would Product Security detect exploitation of an organization-developed product in a customer environment?",
    "follow_ups": [
      "What product telemetry do we receive from customer deployments (with consent)?",
      "What signals would prompt an internal investigation absent a customer report?",
      "What threat intel feeds cover exploitation of PAM/remote-access products specifically?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "What is the process for issuing an emergency product patch or hotfix during an active exploitation event?",
    "follow_ups": [
      "What is the fastest realistic timeline from confirmed vulnerability to released patch?",
      "How is the patch tested under time pressure without regressing other customers?",
      "What is the rollback plan if the patch introduces a regression?",
      "Who authorizes shipping a hotfix outside the normal release cadence?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How does the organization draft, review, and publish a security advisory to customers?",
    "follow_ups": [
      "Who reviews the advisory before publication (Legal, Comms, Engineering, CISO)?",
      "What channels deliver the advisory (CVE listing, customer portal, email, partner channels)?",
      "How are customer-specific mitigations communicated for those who cannot patch immediately?",
      "What is the cadence for follow-up advisories as new information surfaces?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "How does Product Security coordinate with customers who appear to be actively exploited in this scenario?",
    "follow_ups": [
      "What support and forensic assistance does the organization offer affected customers?",
      "How is per-customer information walled off from broader advisories?",
      "What is the boundary between the organization's responsibility and the customer's?"
    ]
  },
  {
    "nist_csf_function": "Recover",
    "question": "After this incident, what changes to the product security program would be proposed, and how are they prioritized against the existing roadmap?",
    "follow_ups": [
      "What metrics (mean time to patch, advisory turnaround, regression rate) would measure improvement?",
      "How would the post-mortem be made externally visible, if at all?",
      "What changes to threat models, fuzzing scope, or pen-test coverage would flow from this?"
    ]
  }
]
```

## Supply Chain & Third-Party (use for supply-chain or vendor-responsibility scenarios)

```json
[
  {
    "nist_csf_function": "Identify",
    "question": "Does the organization apply a cyber supply-chain risk management (C-SCRM) approach to managing third-party risk?",
    "follow_ups": [
      "How is the inventory of critical suppliers maintained?",
      "How are suppliers tiered by risk?"
    ]
  },
  {
    "nist_csf_function": "Identify",
    "question": "What is the role of cybersecurity in the review and selection of third-party vendor support?",
    "follow_ups": [
      "What cybersecurity language is included in vendor contracts (training, notification, audit rights)?",
      "How often are contracts reviewed?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "What level of access do third-party vendors have to the organization's network or data?",
    "follow_ups": [
      "How often are third-party access rights and data logs reviewed?",
      "How is vendor access enforced (remote access controls, jump hosts, time limits)?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "How would the organization detect a breach at a critical vendor before the vendor itself notifies?",
    "follow_ups": [
      "What telemetry from vendor environments do you ingest?",
      "What threat intel feeds cover supply-chain compromises?"
    ]
  },
  {
    "nist_csf_function": "Govern",
    "question": "For vendor-responsibility scenarios, how does the organization verify its software supply chain before customers receive an update?",
    "follow_ups": [
      "What signing, SBOM, and provenance controls are in place?",
      "How are build environments isolated and monitored?",
      "What is the rollback process if a published update is later found compromised?"
    ]
  }
]
```

## Cloud-Specific (use for cloud_compromise scenarios)

```json
[
  {
    "nist_csf_function": "Identify",
    "question": "How is the organization's cloud asset inventory maintained, and how complete is monitoring coverage?",
    "follow_ups": [
      "Which accounts or subscriptions are excluded from monitoring today, and why?"
    ]
  },
  {
    "nist_csf_function": "Detect",
    "question": "How is cloud audit telemetry ingested and retained, and is that retention sufficient for this scenario's investigation horizon?",
    "follow_ups": [
      "What is the latency from cloud event to detection?",
      "What detections specifically cover cloud credential abuse?"
    ]
  },
  {
    "nist_csf_function": "Respond",
    "question": "What does the playbook say about handling exposed cloud credentials, and is key rotation alone sufficient in this scenario?",
    "follow_ups": [
      "What about active sessions and assumed roles?",
      "How are downstream effects (data accessed, persistence established) scoped?"
    ]
  },
  {
    "nist_csf_function": "Identify",
    "question": "How are non-human (service or workload) identities inventoried across the organization's cloud environments, and what is the credential-rotation posture?",
    "follow_ups": [
      "Which workloads still use long-lived static credentials vs. federated workload identity (IRSA, OIDC)?",
      "How are unused or stale machine identities decommissioned, and on what cadence?",
      "Who owns the inventory, and what is its source of truth?"
    ]
  },
  {
    "nist_csf_function": "Protect",
    "question": "How are cross-account and cross-tenant trust relationships audited, and where could lateral movement occur in this scenario?",
    "follow_ups": [
      "What AssumeRole or service-principal trusts exist between prod and non-prod?",
      "How are external (third-party) cross-account roles reviewed?"
    ]
  }
]
```
