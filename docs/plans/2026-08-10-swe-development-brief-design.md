# SWE Development Brief — Design

**Status:** Approved design; implementation not started.

## Problem

Early software development repeatedly loses context: useful prior work is
forgotten, earlier failures are repeated, and ideas from dissimilar repositories
remain invisible. Existing/in-progress repositories have a related problem:
their next step is unclear—continue, mitigate a bounded gap, or re-develop.

CAM_Codx already has a broad command surface and a detailed operator cheat
sheet. It needs a focused, outcome-oriented entry point that turns CAM's
existing knowledge into an actionable development decision without becoming a
dashboard or implicitly running mining, provider calls, or code mutation.

## Product outcome

Provide one concise, provenance-linked **Development Brief** for either:

1. a **new project**; or
2. an **existing/in-progress project** that may need continuation, mitigation,
   or re-development.

The default brief uses only the declared target repository plus CAM's already
mined knowledge. Searching additional local repositories is an explicit,
reviewable expansion—not a hidden background scan or mining run.

## Core interaction

```text
Describe task → choose New or Continue/Rescue → receive brief → choose one next step
```

The first pass is read-only. It does not mine repositories, call a provider,
change a model profile, write to `claw.db`, create a task, edit code, or begin
self-enhancement.

## Brief modes

### New project

Input: a project idea, target path when known, and optional constraints.

The brief returns:

1. closest prior work;
2. clearly labelled cross-domain analogies;
3. reusable components, tests, workflows, and patterns;
4. past failure modes or mistakes worth avoiding;
5. a small, evidence-backed starting plan; and
6. optional local source folders worth searching next.

### Continue/rescue

Input: an existing repository and the requested outcome or concern.

The brief returns:

1. current-state evidence from repository truth files, tests, dirty state,
   visible gaps, and risks;
2. a recommendation to **continue**, **mitigate**, or **re-develop**;
3. the reasons and evidence for that recommendation;
4. relevant lessons/components from prior and dissimilar repositories; and
5. the smallest safe next repair or continuation step with verification.

The recommendation is advice, not an automatic decision. It must be tied to
observable repository evidence and make uncertainty explicit.

## Evidence classes

Every recommendation belongs to exactly one class:

| Class | Meaning | Required rendering |
| --- | --- | --- |
| Direct precedent | Same stack, feature, or failure pattern | Source repo/method, why it matches, confidence |
| Transferable analogy | Dissimilar work with an explained relevant lesson | Source repo/method, explicit transfer rationale, confidence |
| New hypothesis | A novel direction CAM suggests | Validation needed, assumptions, confidence |

The UI must never present an analogy or hypothesis as if it were a direct,
drop-in implementation. Every card states **why this applies here** and links
to its source evidence.

## Next-step model

The brief ends with one recommended next step and a small set of optional,
explicit alternatives:

- inspect a cited source;
- create/update a target `GOAL.md` and implementation plan;
- prepare a bounded mitigation/repair plan;
- perform a scan-only expansion into named local folders; or
- approve a later implementation phase.

The brief should request an expanded search only when default-scope evidence is
thin. It never silently searches a broader folder, mines a repository, or
spends provider budget.

## UX principles

- Optimize for early SWE decisions, not command discovery or novelty.
- Return a short, skimmable brief rather than a dashboard or chat wall.
- Preserve provenance, confidence, and limits at the point of recommendation.
- Prefer a target repository plus existing CAM knowledge by default.
- Keep all mutations and provider-backed operations as explicit later phases.
- Treat repository-native tests and verified current state as stronger evidence
  than historical summaries or generic methodology matches.

## Boundaries

- CAM_CAM remains the owner of CLI, MCP, corpus, mining, models, and runtime
  behavior.
- CAM_Codx owns the new operator workflow, presentation contract, safety
  routing, and evidence template.
- The feature must not depend on an unqualified `cam` executable; moved-checkout
  paths and module provenance remain visible.
- The feature must honour the current relocation gate before any federated or
  multi-ganglion search is offered.
- It must not turn the routine `cam-codx-swe` workflow into implicit mining.

## Acceptance criteria for a future implementation

1. One explicit entry point accepts a mode, task text, and target repository.
2. Default operation is demonstrably read-only and uses target plus existing
   CAM knowledge only.
3. New-project output includes precedent, analogy, mistakes, reuse candidates,
   and a minimal starting plan.
4. Continue/rescue output produces a reasoned continue/mitigate/re-develop
   recommendation with current-state evidence.
5. Every item includes evidence class, source/provenance, why-it-applies text,
   and confidence/limitation.
6. Additional-repository search is off by default and requires explicit named
   scope; live mining remains a separate approval-gated action.
7. A user can choose a next step without reading the full CLI cheat sheet.
8. Tests cover no-mutation default behavior, direct/analogy/hypothesis labels,
   low-evidence expansion prompts, and all three continue/rescue outcomes.

## Deferred work

- A portfolio dashboard.
- Autonomous multi-repository repair.
- Automatic provider use, automatic mining, automatic model promotion, and
  automatic self-enhancement.
- Ranking/retraining from implicit user behavior; any later learning signal
  must be explicit, reviewable, and evidence-backed.
