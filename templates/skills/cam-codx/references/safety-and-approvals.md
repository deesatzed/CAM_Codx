# Safety and Approvals

The capability contract is the policy authority. The manager derives the fixed
argv prefix, CAM_Codx phase, risk, side effects, provider flag, and approval
classes from it; never reconstruct those policies in prose or ad hoc code.

## Approval classes

- `none`: verified read-only route after identities resolve.
- `bounded_phase`: local record/artifact/corpus maintenance within named scope.
- `provider_spend`: exact provider/model/task/time/cost bounds.
- `target_mutation`: exact target repository, task, files, checks, and rollback.
- `configuration_change`: exact config/profile selection and recovery path.
- `promotion`: reviewed candidate, comparison evidence, and rollback receipt.
- `live_cam_mutation`: validated diff plus separate approval for live swap or
  rollback.
- `external_network`: named service, direction, data class, and artifact.

Compound policies require every listed class. Use one matching, unexpired,
single-use approval for the exact packet. A dry run validates but does not
consume that approval.

## MONID external evidence

MONID is an optional external-evidence dependency, not a CAM_CAM command and
not a substitute for an existing dedicated user tool or owned API. An evidence
request names the decision-changing question, allowed source policy, data
class, retention class, freshness rule, and per-task budget before it may run.
The control-plane planner may inspect the local cache without making a provider
call; a cache miss is an evidence gap, not permission to spend.

Cache reuse is permitted only when the new task's source policy, retention
class, question/parameter identity, and freshness rule are compatible. Retain
the raw local response and a redacted receipt, but quarantine sensitive or
policy-violating results from ordinary retrieval. Show evidence, reuse only,
refresh, and do not retain remain user controls.

Do not self-authorize provider spend. A live MONID request requires a known
endpoint price within the declared per-task budget and the relevant external
network/provider-spend authorization. Unknown price, prohibited data class,
private content, secrets, PHI, legal/clinical conclusion, or an unavailable
endpoint fails closed before execution.

## Non-negotiable boundaries

- No implicit mining.
- No implicit promotion.
- Ordinary SWE work never mines.
- Promotion is never part of mining.
- Provider spend, target mutation, configuration/promotion, and live CAM
  mutation never inherit permission from an earlier phase.
- A failed check, rejected candidate, fixture result, or hypothetical idea is
  not verified success.
- Do not print or persist secrets, raw provider responses, private databases,
  or unnecessary target content in receipts.
- Do not execute a packet if contract, wrapper path/content, target, database,
  config, model profile, run, receipt, digest, expiry, or approval identity has
  drifted.

Direct CAM_CAM is a troubleshooting/runtime-development/recovery surface only.
It does not bypass these evidence or approval boundaries.
