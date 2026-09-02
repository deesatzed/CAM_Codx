---
name: cam-codx-monid-launch-week
description: Build a bounded public launch-intelligence brief for an independent developer by using CAM_Codx context and inspected pay-as-you-go Monid endpoints. Use for launch mentions, community signals, and follow-up decisions when no owned monitoring tool covers the request.
---

# CAM_Codx Monid Launch Week

Turn public launch signals into a daily brief and ranked follow-ups without
requiring a standing monitoring subscription. CAM_Codx supplies product context;
Monid may fill a narrowly defined external-data gap.

## Route and plan

1. Read repository truth files. Extract only already-public product name,
   homepage, launch channel, date window, and decision questions.
2. Honor a user-selected source first. Otherwise prefer an existing dedicated
   tool for analytics, email, support, or owned community data. Use Monid only
   for uncovered public-web or public-community evidence.
3. Use public data only. Never send private roadmaps, credentials, unreleased copy, customer data,
   CAM internals, local paths, or other confidential material.
4. Create a no-spend plan with a narrow public subject and 1-5 candidates:

   ```text
   python <CAM_CODEX>/tools/cam_monid_showcase.py \
     --skill cam-codx-monid-launch-week \
     --subject "<public product and date window>" --candidate-limit 5 \
     --max-cost-usd "<ceiling>" --output <artifact>/monid-plan.json
   ```

The helper uses `monid discover` and `monid inspect`. Always inspect before any paid operation.
Confirm `paid_endpoint_executed: false`. Present endpoint health, required inputs,
price model, maximum spend, result limit, and the mention fields to retain.

## Paid collection

The request for a launch brief is not spending authority. Use `monid run` only
after explicit authorization states endpoint, exact public query, call count,
and maximum total cost. Use one call and a small 5-10 item limit, pass list-form
arguments, and save raw output with `-o <artifact>`. Never display API keys.

If the response is asynchronous, poll its identifier through `monid runs` with
a bounded attempt count. On `BLOCKED`, stop and show the reason, money/call
controls, and the exact user action needed. Do not substitute a costlier source.

## Launch brief

Deduplicate mentions by canonical URL. Label source, timestamp, evidence link,
relevance, sentiment as an inference, and recommended owner/action. Separate
observed evidence from CAM_Codx interpretation and identify blind spots. The
brief may recommend outreach or a product change but must not perform either.

Do not publish the brief, contact people, post launch content, mutate the target,
or reveal confidential CAM_Codx methods without separate authorization.
