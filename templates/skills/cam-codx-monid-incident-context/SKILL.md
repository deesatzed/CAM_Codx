---
name: cam-codx-monid-incident-context
description: Add bounded public news, website-health, and mention evidence to a CAM_Codx software incident investigation through inspected pay-as-you-go Monid endpoints. Use only when internal telemetry and existing incident tools leave a specific external-context gap.
---

# CAM_Codx Monid Incident Context

Add external context to an incident timeline without confusing public signals
with root-cause proof. Internal telemetry and the existing incident process stay
authoritative.

## Route and plan

1. Read incident and repository truth files. State the public service identity,
   time window, unresolved question, and evidence cutoff.
2. Honor a user-selected source first. Otherwise prefer an existing dedicated tool
   for observability, status, or incidents. Use Monid only for the specific gap
   in public news, website health, or outage mentions.
3. Use public data only. Never send logs, tokens, IPs, customer data, security findings, local paths,
   CAM internals, or any other confidential incident material.
4. Produce a no-spend plan with 1-5 candidates:

   ```text
   python <CAM_CODEX>/tools/cam_monid_showcase.py \
     --skill cam-codx-monid-incident-context \
     --subject "<public service and time window>" --candidate-limit 5 \
     --max-cost-usd "<ceiling>" --output <artifact>/monid-plan.json
   ```

The helper uses `monid discover` and `monid inspect`. Always inspect before any paid operation.
Check `paid_endpoint_executed: false`; show endpoint health, input schema, price
model, maximum spend, time/result limits, and the exact external question.

## Paid collection

Incident urgency is not spending authority. Use `monid run` only after explicit
authorization states endpoint, exact public input, call count, and maximum total
cost. Use a single bounded call, list-form arguments, and `-o <artifact>`. Never
print provider keys or incident secrets.

For asynchronous results, poll the identifier using `monid runs` with bounded
attempts. On `BLOCKED`, stop and surface the reason and exact user controls; do
not broaden the investigation or silently choose another provider.

## Timeline evidence

Record source URL, publication or observation time, retrieval time, affected
public surface, and confidence. Mark correlations and conflicting timestamps.
An external outage mention or website-health result is context, not causation.
State whether it changes mitigation, follow-up, or neither.

Do not post a status update, contact a vendor, or change production. Do not publish
the incident or disclose confidential CAM_Codx methods without separate authorization.
