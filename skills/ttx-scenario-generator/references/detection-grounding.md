# Grounding Detection References

Use this guide when an inject names a detection, alert, or rule from the user's environment.

## Verify specific detections

Only name a detection rule when the user supplied or authorized an appropriate source, such as a rule repository, alert catalog, or redacted example. Search that source for a rule matching the scenario's technique and relevant platform, then verify the exact name and any severity or behavior included in the scenario.

Never invent a rule name, severity, query, alert routing path, or claim that a control detected an event. Do not copy query contents or sensitive source data into the scenario. If the available source does not confirm a matching rule, keep the trigger generic or use the missing detection as a discussion point.

## Describe an unverified alert generically

When no approved source is available, describe the event at the capability level without naming a product or rule. For example:

```json
{
  "trigger_source": "Endpoint detection alert",
  "title": "Unusual credential access on a finance workstation",
  "narrative": "The endpoint detection team receives an alert for unusual access to credential material. The alert is not yet confirmed as malicious.",
  "indicators": [
    "A workstation accessed credential material outside its usual pattern",
    "The activity occurred shortly before an unfamiliar sign-in"
  ]
}
```

If a verified detection is used, record the source at a safe level of detail in `metadata.grounding_sources_used`. Keep all exercise identifiers and indicators fictional.
