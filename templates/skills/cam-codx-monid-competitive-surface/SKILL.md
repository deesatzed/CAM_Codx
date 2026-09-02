---
name: cam-codx-monid-competitive-surface
description: Map a product's public competitive surface with CAM_Codx context and inspected pay-as-you-go Monid search, brand, company, or news endpoints. Use for a bounded positioning decision, not confidential diligence or broad recurring market surveillance.
---

# CAM_Codx Monid Competitive Surface

Create an evidence-linked competitor and positioning map for one stated product
decision. Do not produce a generic market report or imply exhaustive coverage.

## Route and plan

1. Read repository truth files and define the positioning question, public
   product subject, geography, and time window.
2. Honor a user-selected source. Otherwise prefer an existing dedicated tool for
   search, CRM, analytics, or research already available. Use Monid only for the
   missing public-data surface.
3. Use public data only. Exclude credentials, customer lists, private financials, local files, CAM
   internals, unreleased strategy, and all other confidential material.
4. Produce a no-spend plan with 1-5 candidates:

   ```text
   python <CAM_CODEX>/tools/cam_monid_showcase.py \
     --skill cam-codx-monid-competitive-surface \
     --subject "<public product and market>" --candidate-limit 5 \
     --max-cost-usd "<ceiling>" --output <artifact>/monid-plan.json
   ```

The helper uses `monid discover` and `monid inspect`. Always inspect before any paid operation.
Verify `paid_endpoint_executed: false`; show schema, health, price model, maximum
spend, requested result limit, and why each endpoint is or is not suitable.

## Paid collection

Competitive research does not itself authorize provider spend. Use `monid run`
only after explicit authorization identifies the endpoint, exact public query,
call count, and maximum total cost. Make one bounded call with a 5-10 item limit,
list-form arguments, and `-o <artifact>`. Do not expose provider keys.

For asynchronous work, poll the returned identifier using `monid runs` within a
fixed attempt limit. If `BLOCKED`, stop and report the reason and user controls;
do not increase spend, broaden the query, or silently change endpoints.

## Decision map

Normalize each competitor claim to a public URL and observation date. Distinguish
direct competitors, substitutes, and adjacent tools. Separate observed search,
mention, company, or news facts from positioning inferences. End with the narrow
decision supported, uncertainties, and the cheapest next proof.

Do not publish claims, contact competitors, alter positioning copy, mutate the
target, or disclose confidential CAM_Codx methods without separate authorization.
