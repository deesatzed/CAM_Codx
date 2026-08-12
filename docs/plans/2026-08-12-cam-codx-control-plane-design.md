# CAM_Codx Unified Control Plane Design

**Date:** 2026-08-12  
**Status:** Approved design; implementation not yet complete  
**Owner:** CAM_Codx  
**Runtime dependency:** CAM_CAM

## Purpose

Make CAM_Codx the normal user-facing control plane for every CAM_CAM
capability. Direct CAM_CAM CLI use remains supported for runtime development,
diagnosis, recovery, and regression isolation, but is no longer the normal
product workflow.

The design serves two practical developer needs:

1. use prior work, including analogous and dissimilar repositories, to start
   new projects more efficiently and avoid repeating mistakes;
2. continue, repair, mitigate, or deliberately redevelop in-progress projects
   with traceable evidence from recall through verification.

It also closes the gap between mining repositories and proving that mined
knowledge was actually useful in a later build.

## Current-State Findings

The 2026-08-12 audit found that CAM_CAM already contains most of the required
runtime primitives, but exposes them through a large expert command surface.
Its documented normal front door, `cam chat`, only executes the mining route;
build and enhancement requests are explicitly reported as not wired.

CAM_Codx currently installs four partially overlapping skills:

- `cam-codx-setup`;
- `cam-codx-swe`;
- `cam-codx-development-brief`;
- `cam-codx-pull-mine-dir`.

A separate `cam-codx-session` semantic router also exists outside the install
set. The result is useful functionality without one obvious product entrypoint.

CAM_CAM already has the durable CAM-SEQ structures required for a
source-to-outcome chain:

- `task_plans` and `slot_instances`;
- `component_cards` and `application_packets`;
- `pair_events`, `landing_events`, and `outcome_events`;
- `run_connectomes`, `run_connectome_edges`, and `run_events`;
- `mining_missions` and `compiled_recipes`.

The new UX must activate and explain those structures rather than introduce a
parallel reuse database.

## Product Decision

The normal interaction is:

```text
Developer
   -> CAM_Codx
   -> intent, scope, approvals, and evidence gates
   -> CAM_CAM runtime
   -> claw.db, mining, models, execution, and verification
```

CAM_Codx manages every CAM_CAM feature. CAM_CAM continues to own runtime
implementation and storage. Codex remains responsible for target-repository
judgment, edits, tests, and the final truth claim during normal SWE work.

## One User-Facing Skill

The canonical installed skill will be named `cam-codx`.

The user should be able to say:

```text
Use CAM_Codx to assess this project.
Use CAM_Codx to continue this build.
Use CAM_Codx to troubleshoot this failure.
Use CAM_Codx to find applicable prior work.
Use CAM_Codx to mine this directory for this project.
Use CAM_Codx to verify and record the result.
Use CAM_Codx to inspect or improve CAM itself.
```

Setup, Development Brief, routine SWE, pull/mine, model-management, and
self-enhancement instructions become internal routed playbooks. They remain
separately testable implementation assets but no longer compete as entrypoints
that a developer must remember.

## Everyday SWE Intents

| Intent | Outcome | Default boundary |
| --- | --- | --- |
| `assess` | Understand an idea or repository and recall relevant prior work | Read-only |
| `plan` | Define scope, gaps, risks, checks, and next milestone | Read-only plan artifact |
| `build` | Start or continue a bounded implementation | Prepare first; execute only within the approved task |
| `fix` | Diagnose, mitigate, repair, or recommend redevelopment | Diagnose first; mutation requires the approved fix phase |
| `verify` | Run checks and test claims against evidence | No success claim without passing evidence |
| `record` | Preserve verified success, partial success, failure, and limitations | Preview first; write only in the record phase |

None of these intents implicitly mines repositories, changes a model, promotes
a profile, swaps CAM code, or authorizes unbounded provider spend.

## Complete Capability Routes

CAM_Codx will additionally route:

- explicit repository mining and corpus maintenance;
- knowledge browsing, federation, CAG, and learning reports;
- model catalog, profiles, benchmarks, promotion, and rollback;
- CAM self-enhancement candidate, validation, swap, and rollback;
- champion/challenger evolution;
- security, PULSE, MCP, dashboard, setup, health, and doctor operations;
- Repo Rescue Desk, Repo Necromancer, Forge, A/B, and other supported expert
  workflows.

Every public CAM_CAM command must be classified exactly once as:

1. CAM_Codx-managed;
2. direct troubleshooting/runtime-development only; or
3. hidden compatibility alias.

An unclassified new CAM_CAM command is a contract failure.

## Machine-Readable Capability Registry

CAM_Codx will own one registry that drives routing, approval policy,
documentation, and drift tests. A conceptual entry is:

```yaml
intent: mine
cam_command: [mine]
risk: corpus_write
provider_spend: possible
approval: bounded_phase
default_mode: scan_only
artifacts:
  - mining_receipt
  - corpus_delta
  - integrity_report
legacy_names:
  - mine-workspace
  - mine-all
```

The registry does not duplicate CAM runtime implementation. It records how
CAM_Codx may invoke and explain each runtime operation.

It must be used by:

- the semantic skill router;
- the fixed-operation manager allowlist;
- approval and side-effect summaries;
- generated capability and troubleshooting documentation;
- command coverage and documentation-drift tests.

## Mine-to-Build Evidence Chain

Every managed project engagement receives one durable SWE Run identifier.
CAM_Codx carries it automatically across phases:

```text
source repository
   -> mining receipt
   -> candidate pattern
   -> explicit selection decision
   -> target landing plan
   -> implementation evidence
   -> verification result
   -> recorded outcome
```

### Mining receipt

An explicit mining run records source paths and commits where available,
skips, additions, updates, deduplication, rejection, provider/model, bounded
cost, database integrity, provenance, and a stable receipt identifier. Added
rows alone are not proof of useful mining.

### Assessment labels

Retrieved candidates are classified as:

- **direct precedent**: sufficiently compatible to inspect for reuse;
- **transferable analogy**: a principle from a dissimilar context with an
  explicit transfer rationale;
- **new hypothesis**: plausible but not yet supported.

### Selection decisions

Every candidate is `selected`, `rejected`, `deferred`, or
`needs-inspection`. Retrieval is never silent permission to modify a target.

### Landing map

Every selected candidate names the source pattern, selection reason, target
component, expected adaptation, risk, and verification requirement.

### Verification and recording

Outcomes are `verified_success`, `verified_partial`, `verified_failure`, or
`not_verified`. Only verified outcomes may strengthen trust evidence. Failures
are retained as negative memory and counterexamples; CAM must not convert a
failed check into a positive learning signal.

## Reuse of Existing CAM-SEQ Storage

The user-facing SWE Run is a simpler view over existing CAM_CAM structures:

| User-facing concept | CAM_CAM structure |
| --- | --- |
| Request and plan | `task_plans`, `slot_instances` |
| Reusable candidate | `component_cards` |
| Selection and adaptation plan | `application_packets` |
| Selection or replacement | `pair_events` |
| Target landing | `landing_events` |
| Proof result | `outcome_events` |
| Complete run | `run_connectomes`, edges, and `run_events` |
| Identified acquisition gap | `mining_missions` |
| Repeated verified pattern | `compiled_recipes` |

No new reuse database or parallel run schema will be added initially. If a
later implementation proves that a field cannot be represented without data
loss, the plan must document that gap before proposing a migration.

## Ownership Boundary

### CAM_Codx owns

- semantic intent routing;
- target truth-file inspection;
- capability registry and risk classification;
- fixed-operation packets, phase approvals, and receipts;
- the user-facing SWE Run summary;
- candidate review and landing-map presentation;
- Codex target-repository execution and verification;
- generated help, cheatsheets, and migration guidance.

### CAM_CAM owns

- CLI, MCP, database, retrieval, mining, models, agents, and runtime behavior;
- application-packet and CAM-SEQ persistence;
- provider execution and cost evidence;
- raw validators, benchmarks, self-enhancement, and evolution mechanisms.

CAM_Codx may call or wrap these capabilities. It must not vendor, fork, or
reimplement them.

## Approval Classes

The user's request authorizes only the named bounded phase.

| Class | Examples | Policy |
| --- | --- | --- |
| Read-only | assess, status, corpus query, reports | May run after paths are resolved |
| Local record write | plan artifact, outcome record | Preview scope; write only within the named phase |
| Corpus write/provider spend | live mine, enrich, PULSE ingestion | Explicit source, database, model, time, and cost bounds |
| Target code mutation | build, fix, enhance, create | Explicit task scope and target; repository checks arbitrate |
| Promotion/configuration | model set/use/rollback | Separate single-use approval and rollback receipt |
| CAM live mutation | self-enhance swap/rollback | Separate approval after candidate validation and diff review |

The manager continues to execute list-form arguments without a shell, reject
secret-bearing arguments, bind approvals to a content digest, and consume each
approval once.

## Direct CAM_CAM Use

Direct CAM_CAM commands remain supported for:

- diagnosing CAM_Codx routing;
- isolating a runtime failure;
- testing a raw CAM_CAM capability;
- recovery when CAM_Codx setup is broken;
- CAM_CAM development and regression testing.

They are documented in an operator/troubleshooting reference. Compatibility
aliases remain executable but hidden. `cam chat` remains callable but is no
longer advertised as the normal product front door.

An internal structured CAM_CAM route may be added for CAM_Codx integration,
but it is an implementation seam and troubleshooting surface, not another
workflow the normal user must learn.

## Skill Migration

The setup wizard will eventually install the single canonical `cam-codx`
skill. Existing specialized skill directories will not be silently deleted.
An explicit migration will move known CAM-managed legacy skills to a
timestamped recoverable backup and report the new invocation.

Until that implementation lands, documentation must distinguish:

- **current:** four setup-installed skills plus the separate session-router
  artifact;
- **approved target:** one `cam-codx` skill with internal playbooks.

## User-Facing Status Card

Before action, CAM_Codx should show:

```text
Goal: Diagnose and repair the failing search-agent tests
Route: fix
Target: /path/to/project
CAM memory: read-only recall
Writes: target repository after approval
Provider spend: none
Mining: no
Next action: diagnose
```

After action, it should report CAM evidence used, changes made, checks run,
verified result, learning eligibility, and remaining risk. Raw commands remain
available in the receipt rather than dominating the normal UX.

## Documentation Strategy

Active documentation uses the current layout:

- CAM_Codx: `/Volumes/WS4TB/waswiki/CAM_Codx`;
- CAM_CAM: `/Volumes/WS4TB/waswiki/CAM_CAM`;
- default mining pool:
  `/Volumes/WS4TB/waswiki/repos2mine/repo622sn`.

Historical evidence retains its original paths, with a historical label when
needed. Docs must not claim that the canonical one-skill router exists until
the implementation and migration tests pass.

## Acceptance Gates

The implementation is complete only when:

1. every public CAM_CAM command is classified by the CAM_Codx registry;
2. no visible duplicate alias appears in normal help;
3. one skill routes the six SWE intents and every administrative capability;
4. read-only requests cause no repository, corpus, model, or config writes;
5. mining requires an explicit request and produces a verified delta receipt;
6. model promotion and live CAM swap require separate single-use approval;
7. failed verification cannot become a successful outcome;
8. help, cheatsheet, skill, registry, and implementation agree mechanically;
9. existing expert scripts using legacy commands continue to work;
10. focused and full CAM_Codx/CAM_CAM verification passes.

## Real Proof Scenario

The end-to-end proof will use the already mined MatrAIx-Persona-8B and SESA
sources to design a bounded evolutionary population-testing vertical slice.
The proof must identify what was actually learned, select and reject candidates
with provenance, create a landing map, implement and verify the slice, record
the outcome, and show that a later CAM_Codx assessment retrieves that outcome.

This scenario demonstrates both product priorities: effective mine-to-build
use and creation of something novel and useful.

## Non-Goals

- Removing expert CAM_CAM commands or breaking scripts.
- Making normal SWE work implicitly mine or self-enhance.
- Treating lexical or embedding overlap as causal proof.
- Replacing CAM_CAM persistence with CAM_Codx-owned databases.
- Claiming the MatrAIx/SESA product is built before its separate implementation
  and verification gates pass.
