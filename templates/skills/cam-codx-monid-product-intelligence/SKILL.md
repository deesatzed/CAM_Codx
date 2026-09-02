---
name: cam-codx-monid-product-intelligence
description: Design and test a provider-independent public product-data adapter using CAM_Codx context and inspected pay-as-you-go Monid price, inventory, detail, or review endpoints. Use for a bounded application feature, not purchasing or scraping private account data.
---

# CAM_Codx Monid Product Intelligence

Prove whether public price, inventory, detail, or review data can support one
application feature. Produce a normalized adapter fixture and evidence limits,
not a provider-specific architecture commitment.

## Route and plan

1. Read repository truth files. Define the product identifier, public market,
   freshness need, normalized fields, and feature acceptance test.
2. Honor a user-selected source first. Otherwise prefer an existing dedicated tool
   for commerce or catalog data. Use Monid only for the uncovered requirement.
3. Use public data only. Exclude credentials, carts, accounts, customer history,
   source code, local paths, CAM internals, and other confidential material.
4. Create the no-spend plan with 1-5 candidates:

   ```text
   python <CAM_CODEX>/tools/cam_monid_showcase.py \
     --skill cam-codx-monid-product-intelligence \
     --subject "<public product identifier and market>" --candidate-limit 5 \
     --max-cost-usd "<ceiling>" --output <artifact>/monid-plan.json
   ```

The helper performs `monid discover` and `monid inspect`. Always inspect before
any paid operation. Require `paid_endpoint_executed: false`; show required inputs, health,
price model, maximum spend, limit controls, and proposed normalization fields.

## Paid fixture

Building the feature does not authorize provider spend. Use `monid run` only
after explicit authorization specifies endpoint, exact public product input,
call count, and maximum total cost. Use one call and the smallest result limit,
list-form arguments, and `-o <artifact>`. Never print keys or secrets.

If asynchronous, poll the identifier using `monid runs` with bounded attempts.
On `BLOCKED`, stop and expose the reason and exact user controls. Do not switch
to a more expensive endpoint or execute a purchase.

## Adapter evidence

Normalize source, product identifier, observed-at time, currency, price,
availability/inventory state, review aggregate, and evidence URL when present.
Represent missing fields explicitly. Test the adapter against the saved fixture
and label freshness, geographic, availability, and terms-of-use limitations.

Do not buy products. Do not publish derived data, mutate the target application, or
expose confidential CAM_Codx methods without separate authorization.
