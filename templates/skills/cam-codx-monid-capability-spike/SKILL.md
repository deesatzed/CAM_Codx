---
name: cam-codx-monid-capability-spike
description: Evaluate a missing public-data capability for a CAM_Codx build by discovering and inspecting pay-as-you-go Monid endpoints, then produce an evidence-backed adapter go/no-go decision. Use for bounded integration spikes, not routine work already served by an existing tool.
---

# CAM_Codx Monid Capability Spike

Decide whether a missing external-data capability is worth integrating. Produce
a small adapter contract, fixture, cost envelope, and go/no-go recommendation;
do not turn discovery into an open-ended provider evaluation.

## Route and plan

1. Read repository truth files and state the exact capability gap.
2. Honor a user-selected tool first. Otherwise prefer an existing dedicated tool
   that already satisfies the request. Use Monid only for the uncovered gap.
3. Restrict the subject to public data. Never send credentials, source code,
   private paths, customer data, CAM internals, or other confidential material.
4. Create the no-spend plan with one narrow query and 1-5 candidates:

   ```text
   python <CAM_CODEX>/tools/cam_monid_showcase.py \
     --skill cam-codx-monid-capability-spike \
     --subject "<public capability subject>" --candidate-limit 5 \
     --max-cost-usd "<ceiling>" --output <artifact>/monid-plan.json
   ```

The helper uses `monid discover` and `monid inspect`. Always inspect before any paid operation.
Confirm the artifact says `paid_endpoint_executed: false`. Show provider,
endpoint, health, input schema, price model, maximum spend, rejected candidates,
and the proposed smallest fixture before asking to continue.

## Paid proof

A general request to build or use this skill is not spending authority. Run
`monid run` only after explicit authorization names the endpoint, exact input,
call count, and maximum total cost. Use list-form arguments, a single call, the
smallest useful result limit, and `-o <artifact>`. Do not print keys or full
environment values.

For an asynchronous response, use the returned run identifier with `monid runs`
and bounded polling. Stop at the authorized cost or call count. If the command
reports `BLOCKED`, preserve the artifact and surface the blocked reason plus the
exact user-controlled remedy; do not silently switch providers or raise spend.

## Decision evidence

Normalize the minimum response fields into a provider-independent fixture. Test
the adapter against that saved fixture, record latency and actual charge, and
compare it with the existing-tool and no-integration options. The final go/no-go
must separate fixture proof from a live paid proof.

Do not publish results, mutate the target application, store a provider token,
or expose confidential CAM_Codx methods without separate authorization.
