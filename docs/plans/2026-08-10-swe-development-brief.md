# SWE Development Brief Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give a developer working on a new or in-progress repository one short,
provenance-linked Development Brief that surfaces relevant CAM knowledge and
repository evidence, recommends the smallest safe next step, and makes broader
searches or mutations explicit later choices.

**Architecture:** CAM_Codx owns the brief contract, target-repository inspector,
renderer, Codex skill, and user-facing safety routing.  CAM_CAM owns a new
side-effect-free local retrieval API/CLI whose read-only SQLite connection never
records a retrieval, creates a sidecar, invokes a provider, or touches a
federated sibling.  The default brief calls that primary-corpus API and reads
only the named target.  An explicit named-source expansion is a separate
scan-only phase; it is prepared but never auto-run by the default brief.

**Tech Stack:** Python 3.11+ standard library and pytest in CAM_Codx; Python,
Typer, aiosqlite/SQLite URI read-only mode, and pytest in CAM_CAM; JSON Lines
between the runtime retrieval command and CAM_Codx; Markdown for the rendered
brief and Codex skill.

---

## Non-negotiable behavior

- Default execution accepts `--mode new` or `--mode continue-rescue`, task text,
  and an optional named target directory; it returns Markdown to stdout and
  performs no writes.
- It never mines a repository, calls a provider, records retrieval telemetry,
  changes model/configuration, runs tests, creates a CAM task, or starts
  self-enhancement.
- The default retrieval scope is only CAM_CAM's primary, explicitly supplied
  `claw.db`.  Federated siblings are excluded until relocation is fixed and the
  operator names an expansion scope.
- A direct precedent, transferable analogy, and new hypothesis are distinct
  evidence classes.  None may be rendered as a drop-in solution without a
  source, applicability rationale, confidence, and limit.
- Continue/rescue produces an advisory `continue`, `mitigate`, or `re-develop`
  recommendation only from observable evidence.  Missing verification is shown
  as missing, never converted to an invented test result.
- A file is written only when the operator provides `--output <path>`; that
  write is explicitly tested and labelled.

## Task 1: Establish the typed brief contract and red tests in CAM_Codx

**Files:**

- Create: `/Volumes/WS4TB/waswiki/CAM_Codx/tools/development_brief.py`
- Create: `/Volumes/WS4TB/waswiki/CAM_Codx/tests/test_development_brief.py`

**Step 1: Write the failing contract tests.**

Add focused tests for immutable dataclasses (or equivalent explicit dict
schemas) named `BriefRequest`, `EvidenceItem`, `TargetEvidence`, and
`DevelopmentBrief`.  The tests must assert that:

- `new` and `continue-rescue` are the only accepted modes;
- every evidence item has exactly one of `direct_precedent`,
  `transferable_analogy`, or `new_hypothesis`;
- every item contains a source identifier, source kind, applicability text,
  confidence in `[low, medium, high]`, and an explicit limitation;
- a brief has exactly one recommended next step plus separately labelled
  optional next steps; and
- invalid modes, blank task text, or an unclassified evidence item fail before
  any target or CAM access occurs.

**Step 2: Run the new test to verify it fails.**

Run:

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
```

Expected: failure because the module and contract do not yet exist.

**Step 3: Implement only the pure contract and deterministic Markdown renderer.**

Keep this first implementation free of filesystem access and subprocess calls.
Render the sections in this order: purpose/scope; target evidence; direct
precedents; transferable analogies; new hypotheses; reuse and avoid lists;
recommendation; one next step; limitations; and optional explicit expansions.
Render `No CAM evidence retrieved` rather than fabricating a match.

**Step 4: Run the focused test.**

Run the command from Step 2.

Expected: pass with no filesystem writes.

**Step 5: Commit the contract slice.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
git add tools/development_brief.py tests/test_development_brief.py
git commit -m "feat: add development brief contract"
```

## Task 2: Add a read-only CAM_CAM primary-corpus retrieval seam

**Files:**

- Create: `/Volumes/WS4TB/waswiki/CAM_CAM/src/claw/briefing/read_only_query.py`
- Create: `/Volumes/WS4TB/waswiki/CAM_CAM/tests/test_read_only_brief_query.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_CAM/src/claw/cli/_monolith.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_CAM/src/claw/cli/__init__.py` only if it
  needs explicit command registration
- Modify: `/Volumes/WS4TB/waswiki/CAM_CAM/README.md` or the current CLI guide
  with one truthful command reference

**Step 1: Write the failing runtime tests.**

Build a temporary SQLite fixture containing the minimum `methodologies` and
`methodology_fts` schema/data needed to exercise FTS retrieval.  Test a new
`cam brief-query` command/function with this exact observable contract:

- input: `query`, `--db <path>`, `--limit`, and `--json`;
- output JSON object: `schema_version`, `scope: "primary_only"`, `query`, and
  `results` whose records include methodology ID, problem description, notes,
  tags, language, lifecycle state, and text-match score;
- an existing read-only DB is opened using SQLite URI `mode=ro` and
  `immutable=1` (or the platform-equivalent verified no-write mode);
- no `-wal`, `-shm`, journal, or any database row/mtime changes occur;
- malformed query, missing database, or unavailable FTS produces structured
  error JSON and a nonzero exit without creating a database; and
- it does not construct `ClawFactory`, `SemanticMemory`, `EmbeddingEngine`, a
  federation object, or a provider client.

Add an explicit regression test documenting why the existing
`claw_query_memory` MCP handler is not used: it records retrieval usage.

**Step 2: Run the focused runtime test to verify it fails.**

Run:

```bash
cd /Volumes/WS4TB/waswiki/CAM_CAM
PYTHONPATH=src python -m pytest -q tests/test_read_only_brief_query.py
```

Expected: failure because `brief-query` does not exist.

**Step 3: Implement the narrow query module and CLI command.**

Use parameterized FTS queries and a read-only URI.  Do not reuse
`DatabaseEngine`, `ClawFactory`, `learn search`, `kb search`, or
`claw_query_memory`; those paths do not prove the no-write contract and some
can include side effects or federation.  Keep ranking limited to the returned
FTS score; CAM_Codx will label relevance and certainty rather than treating a
rank as validation.

**Step 4: Run the targeted test and command smoke.**

Run:

```bash
cd /Volumes/WS4TB/waswiki/CAM_CAM
PYTHONPATH=src python -m pytest -q tests/test_read_only_brief_query.py
PYTHONPATH=src python -m claw.cli brief-query --help
```

Expected: tests pass and help exposes only local, primary-database parameters.

**Step 5: Commit the runtime seam separately.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_CAM
git add src/claw/briefing/read_only_query.py src/claw/cli/_monolith.py src/claw/cli/__init__.py tests/test_read_only_brief_query.py README.md
git commit -m "feat: add read-only development brief query"
```

Only stage files that actually changed; do not stage `claw.db`, WAL/SHM files,
environment files, or unrelated worktree changes.

## Task 3: Inspect the named target without changing it

**Files:**

- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tools/development_brief.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tests/test_development_brief.py`

**Step 1: Write failing inspector tests using temporary repositories.**

Cover a non-Git directory, a clean Git target, a dirty Git target, a target
with selected truth files, and a target with detectable gap markers.  The
inspector may read only these recognised files when present:
`GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`,
`TASK_QUEUE.md`, and `AGENTS.md`.  It may run `git status --short --branch`
with an argv list and a short timeout.  It must never execute a repository test
command, formatter, package manager, or hook.

Tests must prove the inspector:

- reports read files, Git status, visible `TODO`/`FIXME`/`NotImplemented`
  markers, and missing truth surfaces as evidence rather than claims;
- preserves dirty-state evidence verbatim enough to identify the affected
  paths, without adding/committing/modifying them;
- returns `verification not run` when no test receipt is supplied; and
- rejects a target outside an explicitly provided target path rather than
  discovering sibling repositories.

**Step 2: Run the focused test to verify it fails.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
```

Expected: failure for missing inspector behavior.

**Step 3: Implement `inspect_target_read_only`.**

Bound text reads by size and redact/omit credential-shaped filenames and
values.  Return plain facts and uncertainty flags, not a quality score.  Treat
`TODO` counts as leads for inspection, not proof of an implementation gap.

**Step 4: Implement deterministic Continue/Rescue advice.**

Add a small, explainable rule table:

| Observable state | Advice | Required limitation |
| --- | --- | --- |
| no structural red flags and a current successful test receipt | continue | brief does not prove product completeness |
| bounded named gaps, dirty work, or unverified checks with a coherent target | mitigate | verification or repair is still required |
| missing/contradictory truth, unusable target, or dominant structural risk | re-develop | recommendation is advisory and needs human review |

If evidence is insufficient, choose `mitigate` with a next step to gather
evidence; never label it `continue` merely because inspection succeeded.

**Step 5: Re-run the focused tests and commit.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
git add tools/development_brief.py tests/test_development_brief.py
git commit -m "feat: inspect targets for development briefs"
```

## Task 4: Retrieve, classify, and render evidence with provenance

**Files:**

- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tools/development_brief.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tests/test_development_brief.py`
- Create: `/Volumes/WS4TB/waswiki/CAM_Codx/tests/fixtures/development_brief_results.json`

**Step 1: Write failing adapter and classification tests.**

Use the JSON fixture as a fake `cam brief-query --json` response; no test may
depend on the operator's real `claw.db`.  Test that CAM_Codx invokes a supplied
`--cam-command` only as an argv list and only with a supplied `--cam-db`.
Include a timeout and assert no shell is used.

For a Python retry request, assert that:

- a same-language/result-tagged retry methodology becomes a direct precedent;
- a dissimilar transactional-recovery methodology can become a transferable
  analogy only when its explicit transfer rationale is supplied; and
- a proposed new pattern with no source method becomes a new hypothesis with a
  validation requirement.

Test that low or zero CAM retrieval produces an expansion suggestion naming no
folders by default.  Test that the renderer includes methodology ID/source,
why-it-applies text, confidence, and limitation for every item.

**Step 2: Run the focused test to verify it fails.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
```

Expected: failure because the read-only runtime adapter/classifier is absent.

**Step 3: Implement `query_primary_corpus_read_only` and classifiers.**

The adapter must require an explicit absolute CAM database path or fail with a
clear setup message; it must not fall back to an unqualified `cam` binary or a
historical `repo622sn` path.  Validate the returned JSON schema before
rendering it.  Keep raw source code out of the brief by default; render a
source ID and a concise description instead, so the user elects to inspect the
source before reuse.

Classify as direct only with explicit compatible evidence (such as task/stack
overlap); otherwise classify as analogy or hypothesis.  A score alone is never
sufficient to call an item direct.

**Step 4: Re-run tests and the isolated command smoke.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
python tools/development_brief.py --help
```

Expected: tests pass; help says default scope is target plus primary CAM
knowledge and describes no-write behavior.

**Step 5: Commit the recall slice.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
git add tools/development_brief.py tests/test_development_brief.py tests/fixtures/development_brief_results.json
git commit -m "feat: recall CAM evidence for development briefs"
```

## Task 5: Ship the explicit CLI, skill, and operator guidance

**Files:**

- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tools/development_brief.py`
- Create: `/Volumes/WS4TB/waswiki/CAM_Codx/templates/skills/cam-codx-development-brief/SKILL.md`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/templates/skills/cam-codx-swe/SKILL.md`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tools/cam_setup_wizard.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tests/test_cam_setup_wizard.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/docs/CAM_CHEATSHEET.md`
- Create: `/Volumes/WS4TB/waswiki/CAM_Codx/docs/CAM_DEVELOPMENT_BRIEF.md`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/README.md`

**Step 1: Add failing CLI/setup/skill tests.**

Test exact commands for a new and a continue-rescue request using a fake CAM
command fixture:

```bash
python tools/development_brief.py new \
  --task "Build a durable import retry flow" \
  --target-repo /path/to/project \
  --cam-command /absolute/path/to/cam \
  --cam-db /absolute/path/to/claw.db

python tools/development_brief.py continue-rescue \
  --task "Decide the smallest safe next repair" \
  --target-repo /path/to/project \
  --cam-command /absolute/path/to/cam \
  --cam-db /absolute/path/to/claw.db
```

Assert default stdout mode produces no file changes in the target, CAM_Codx
state directory, or CAM database fixture.  Assert `--output` writes exactly one
user-named Markdown file outside the target by default.  Assert the setup
wizard installs the new skill and preserves the prior setup/SWE skills.

**Step 2: Run the focused tests to verify failure.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py tests/test_cam_setup_wizard.py
```

Expected: failure until the CLI, skill installation, and documentation wiring
exist.

**Step 3: Implement the narrow interaction.**

`cam-codx-development-brief` must ask Codex to obtain task/mode/target and
then call the explicit CLI; it must never auto-run for every SWE task.  Update
`cam-codx-swe` to recommend this skill when the user explicitly asks for prior
work, early-stage reuse, continuation, rescue, or re-development advice.  It
may not make mining, provider spend, or a mutation implicit.

The documentation must put these plain-language prompts first:

```text
Use cam-codx-development-brief to help me start this new project from relevant prior work.
Use cam-codx-development-brief to decide whether this in-progress repository should continue, be mitigated, or be re-developed.
```

Document the explicit `--output`, named-source expansion, and later approval
paths separately.  Do not expose the full CAM CLI as the first UX.

**Step 4: Re-run the focused tests and skill validation.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py tests/test_cam_setup_wizard.py
python tools/validate_skill_frontmatter.py templates/skills/cam-codx-development-brief/SKILL.md
```

Expected: passing tests and valid skill frontmatter.

**Step 5: Commit the UX slice.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
git add tools/development_brief.py templates/skills/cam-codx-development-brief/SKILL.md templates/skills/cam-codx-swe/SKILL.md tools/cam_setup_wizard.py tests/test_development_brief.py tests/test_cam_setup_wizard.py docs/CAM_CHEATSHEET.md docs/CAM_DEVELOPMENT_BRIEF.md README.md
git commit -m "feat: add CAM development brief workflow"
```

## Task 6: Gate explicit expansion and protect the relocation boundary

**Files:**

- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tools/development_brief.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/tests/test_development_brief.py`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/docs/CAM_DEVELOPMENT_BRIEF.md`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/DECISIONS.md`
- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/PROGRESS.md`

**Step 1: Write failing expansion-boundary tests.**

Test that `--source-root` is rejected unless each path is explicitly named,
exists, and remains below an operator-supplied approved parent.  The default
brief must not call `cam federate`, `cam kb search`, `cam mine`, `cam
mine-workspace`, `cam preflight`, or any provider-backed command.  Test that
the current stale sibling paths in CAM_CAM's `claw.toml` cause the expansion
offer to display `relocation gate not satisfied` rather than attempting a
federated query.

**Step 2: Run the test to verify failure.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
```

Expected: failure until the explicit expansion validator and relocation check
are implemented.

**Step 3: Implement a plan-only expansion card.**

Do not implement repository scanning or mining in this feature.  Render named
source folders as a proposed scan-only later phase with a reason, scope, and
the required human approval.  When the relocation gate fails, identify the
configuration mismatch without changing `claw.toml`.

**Step 4: Run tests and a forbidden-command source scan.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_development_brief.py
rg -n "\b(mine|mine-workspace|mine-all|federate|preflight|self-enhance)\b" tools/development_brief.py templates/skills/cam-codx-development-brief/SKILL.md
```

Expected: tests pass; scan shows only explanatory prohibited/deferred language,
never a subprocess command construction.

**Step 5: Commit the safety gate.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
git add tools/development_brief.py tests/test_development_brief.py docs/CAM_DEVELOPMENT_BRIEF.md DECISIONS.md PROGRESS.md
git commit -m "feat: gate development brief expansions"
```

## Task 7: Verify both repositories and publish intentionally

**Files:**

- Modify: `/Volumes/WS4TB/waswiki/CAM_Codx/PROGRESS.md`
- Modify: `/Volumes/WS4TB/waswiki/CAM_CAM/PROGRESS.md`

**Step 1: Run CAM_Codx verification.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q -p no:cacheprovider tests
python tools/generate_agent_packs.py --check
git diff --check
git status --short --branch
```

Expected: all tests pass, generated packs are current, no whitespace errors,
and only deliberate work is present.

**Step 2: Run CAM_CAM verification.**

```bash
cd /Volumes/WS4TB/waswiki/CAM_CAM
PYTHONPATH=src python -m pytest -q tests/test_read_only_brief_query.py tests/test_tool_schemas.py tests/test_integration_wiring.py
PYTHONPATH=src python -m claw.cli brief-query --help
git diff --check
git status --short --branch
```

Expected: all listed tests pass, help works, and no database/WAL/SHM or
private-env files are staged.

**Step 3: Perform a no-mutation proof on a copied test database.**

Copy only a synthetic test fixture database to a temporary directory, record
its SHA-256 digest and directory contents, run `brief-query`, then compare the
digest and files.  This is a fixture proof, not a claim about a live corpus.

**Step 4: Update durable truth and commit only those updates.**

Record exact commands, tests, results, known limitation (primary-only
retrieval), and the relocation-gated expansion behavior.  Do not claim that
new or ongoing projects are automatically fixed; the brief is an evidence
input and next-step recommendation.

**Step 5: Publish only after the user asks.**

Commit CAM_Codx and CAM_CAM separately with their actual files, inspect both
staging areas, and push only when the user explicitly authorizes publication.
Never include the unrelated untracked `docs/CAM_CHEATSHEET.md` unless it has
been reviewed as part of the deliberate documentation scope.
