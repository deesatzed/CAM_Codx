---
name: cam-codx
description: Manage software ideas, new or continuing builds, debugging, troubleshooting, verification, and explicit CAM knowledge, mining, model, evolution, self-enhancement, doctor, or setup work through CAM_Codx with prior-work recall, fixed operation packets, evidence gates, and bounded approvals. Use when Codex should apply CAM evidence to an SWE task, mine named repositories, or manage a named CAM operation; ordinary Codex work remains available when CAM is absent.
---

# CAM_Codx

Use CAM_Codx as the normal control plane for CAM-assisted software work. Keep
Codex responsible for engineering judgment, edits, and verification; keep
CAM_CAM responsible for runtime behavior, the corpus, providers, and models.

## Required order

1. Inspect the target repository. Read `AGENTS.md`, `GOAL.md`, `STANDARDS.md`,
   `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md` when
   present. Treat those truth files as authoritative.
2. Resolve absolute identities for the target, CAM command, `claw.db`,
   `claw.toml`, optional model profiles, setup-generated wrapper, and manager
   state. Stop on split or unresolved identities.
3. Run the read-only planner before preparing anything:

   ```text
   python <CAM_CODEX>/tools/cam_control_plane.py plan \
     --intent <intent> --target <absolute-target> --request <request> \
     --cam-command <absolute-cam> --cam-db <absolute-claw.db> \
     --cam-config <absolute-claw.toml>
   ```

4. Show the plan card: goal, route, target, memory mode, writes, provider
   spend, mining, approval, and next action. Free text uses only the capability
   contract default; pass an explicit operation for any non-default route.
5. For an executable phase, prepare the exact canonical command path through
   the contract-driven manager:

   ```text
   python <CAM_CODEX>/tools/cam_manager.py prepare "<canonical command path>" \
     --wrapper <trusted-wrapper> --state-dir <manager-state>
   python <CAM_CODEX>/tools/cam_manager.py approve <packet> \
     --state-dir <manager-state>
   python <CAM_CODEX>/tools/cam_manager.py execute <packet> \
     --approval <approval> --wrapper <trusted-wrapper> \
     --state-dir <manager-state>
   ```

   Omit approval only when the capability contract declares `none`.
6. Inspect CAM evidence; select or reject it explicitly. Create a landing map
   before adapting a recalled component into the target.
7. Perform the bounded Codex edit, run target-owned checks, and distinguish
   fixture, smoke, and live evidence.
8. Record only the verified outcome, failure, partial result, and limitations.

## Intent router

Use one everyday SWE intent:

- `assess`: understand the idea/repository and recall relevant prior work.
- `plan`: define the smallest milestone, gaps, risks, and checks.
- `build`: start or continue a bounded implementation.
- `fix`: diagnose, mitigate, repair, or recommend re-development.
- `verify`: test the result and its claims.
- `record`: preserve a verified outcome with provenance and limitations.

For the detailed new-project, in-progress, rescue, candidate-selection,
landing, build, fix, verify, and record flows, read
[references/swe-playbooks.md](references/swe-playbooks.md).

Use an administrative family only when explicitly requested:

- `mine`: add knowledge from named sources under cost/time/model bounds.
- `knowledge`: inspect or maintain existing CAM knowledge.
- `models`: inspect, compare, select, promote, or roll back models/profiles.
- `self-enhance`: evaluate a candidate; live swap is a later approval.
- `evolution`: inspect or manage champion/challenger evolution.
- `doctor`: diagnose runtime, security, configuration, or environment health.
- `setup`: install or repair CAM_Codx and CAM_CAM.

For recall, evidence quality, and mining, read
[references/knowledge-playbooks.md](references/knowledge-playbooks.md). For
models, self-enhance, evolution, doctor, and setup, read
[references/admin-playbooks.md](references/admin-playbooks.md).

## Hard boundaries

Ordinary SWE work never mines repositories. There is no implicit mining and no
implicit promotion. Mining, provider spend, target mutation, model/configuration
promotion, and live CAM mutation use their declared approval classes.
Promotion is never part of mining, and live swap or rollback always requires a
separate approval after validation. Use one matching, unexpired, single-use
approval for each bounded packet.

Read [references/safety-and-approvals.md](references/safety-and-approvals.md)
before any write, provider call, promotion, or live operation. Treat direct
CAM_CAM use as a troubleshooting, runtime-development, recovery, or regression
isolation surface—not the normal workflow.
