# SWE Playbooks

Use these flows after reading repository truth and producing a control-plane
plan. CAM evidence proposes; Codex decides; repository checks arbitrate.

## New project

1. Use `assess` to state the idea, user need, constraints, and target.
2. When prior, adjacent, cloned, or dissimilar builds could help, invoke
   `cam-codx-development-brief`. Keep unavailable or stale evidence labeled.
3. Separate candidates into `selected`, `rejected`, and `needs investigation`.
   Cite source repository/component, evidence, fitness, failures, and license
   status. Similarity alone is not a reason to select.
4. Use `plan` to define one smallest useful milestone and its proof.
5. Write a landing map before `build`:

   | Evidence | Source component | Adaptation | Target location | Check |
   | --- | --- | --- | --- | --- |

## In-progress build

1. Reconcile the working tree, truth files, current tests, and last verified
   outcome. Do not treat planned features as implemented.
2. Use `assess` for evidence related to the remaining gap, not the entire idea.
3. Decide whether to continue the present design, mitigate one gap, or choose
   bounded re-development. Preserve user changes and explicit deferrals.
4. Use `plan`, then `build` the next coherent slice only.

## Rescue, mitigation, or re-development

1. Reproduce the failure and classify it: implementation defect, architecture
   gap, dependency/environment drift, missing evidence, or stale direction.
2. Use `cam-codx-development-brief` for prior fixes and failures, including
   lessons from dissimilar repositories.
3. Use `fix` to diagnose before mutation. Rank continue, mitigate, repair,
   replace, and re-development options by evidence and cost.
4. Keep rejected approaches and why they failed. A past failure is useful
   negative evidence, not a positive recipe.

## Troubleshoot

Use `fix` for target-repository troubleshooting. Use `doctor` for CAM_Codx or
CAM_CAM identity, wrapper, contract, database, configuration, provider, model,
or environment problems. Use direct CAM_CAM only when isolating the runtime
from CAM_Codx is itself the diagnostic step.

## Build or fix

1. Freeze exact target, task scope, files, checks, and rollback.
2. Prepare the selected canonical route. Obtain the declared provider-spend or
   target-mutation approval before execution.
3. Adapt only the selected landing-map entries. Do not copy a whole donor repo
   when one method or component is sufficient.
4. Run focused checks, then broader regression checks proportional to risk.

## Verify and record

1. Use `verify` to compare the result with the named acceptance condition.
2. Classify evidence honestly: fixture, synthetic, smoke, integration, or live.
3. Use `record` only after checks. Record the verified outcome, partial result,
   failure, limitations, applied evidence, rejected candidates, and landing
   result. Failed verification cannot become positive evidence.
4. Start a later `assess` only after recording; confirm retrieval retains
   provenance and does not promote rejected or hypothetical candidates.
