# Optional Monid Showcase Playbooks

These optional skills demonstrate how CAM_Codx can fill a narrow public-data
gap with inspected, pay-as-you-go Monid endpoints. They do not replace the
canonical `cam-codx` control plane or grant authority to spend money.

## Outcome router

- Use `cam-codx-monid-capability-spike` to test a missing data capability and
  produce a provider-independent adapter fixture plus a go/no-go decision.
- Use `cam-codx-monid-launch-week` for a cost-capped public mention brief and
  ranked launch follow-ups.
- Use `cam-codx-monid-competitive-surface` for an evidence-linked competitor
  and positioning map supporting one product decision.
- Use `cam-codx-monid-product-intelligence` to test public price, inventory,
  detail, or review data behind a normalized application adapter.
- Use `cam-codx-monid-incident-context` when internal telemetry leaves a
  specific public news, website-health, or outage-mention gap.

Honor a user-selected tool first, then an existing dedicated tool. Route to
Monid only for the uncovered requirement. If none of the five outcomes fits,
continue ordinary CAM_Codx work without Monid.

## Zero-spend planning gate

Create the plan through the shared helper:

```text
python <CAM_CODEX>/tools/cam_monid_showcase.py \
  --skill <showcase-skill> --subject "<public subject>" \
  --candidate-limit 5 --max-cost-usd "<ceiling>" \
  --output <artifact>/monid-plan.json
```

The helper may use only discovery and inspection. Require
`paid_endpoint_executed: false`, and show the endpoint, health, schema, price
model, maximum cost, and rejected candidates. Do not send credentials, local
paths, source code, private product plans, customer data, CAM internals, or
other confidential material.

## Paid proof gate

The original task request is not provider-spend approval. A paid call requires
later explicit authorization naming the selected endpoint, exact public input,
call count, result limit, and total cost ceiling. Save output to a bounded
artifact, stop on `BLOCKED`, and never expand scope or switch providers
silently. Publication, outreach, target mutation, production action, and
deployment remain separate decisions.
