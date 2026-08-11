# Pull, Mine, and Review CAM Skill Design

- **Status:** Approved 2026-08-11
- **Owner:** CAM_Codx workflow layer
- **Runtime owner:** CAM_CAM

## Outcome

Add a Codex skill, displayed to users as `CAM_Codx_Pull_Mine_Dir`, that keeps a
named repository directory current, mines its changed repositories into one
explicit CAM corpus, and explains whether the newly mined evidence warrants a
supervised CAM self-improvement candidate.

The default source root is:

```text
/Volumes/WS4TB/waswiki/repos2mine/repo622sn
```

Any user can replace it with an explicit `--source-root` directory. The
workflow must not rely on this machine's path after setup.

## Chosen Architecture

Use an installable Codex skill backed by a deterministic CAM_Codx coordinator:

```text
CAM_Codx_Pull_Mine_Dir skill
        |
        v
tools/cam_pull_mine_dir.py
        |-- Git discovery / clean fast-forward updates
        |-- CAM scan-only preflight
        |-- bounded live CAM mining
        |-- integrity / delta evidence
        |-- meaningful-mining assessment
        `-- optional supervised candidate through cam_manager.py
```

The coordinator owns validation, argument construction, receipts, and report
rendering. It does not reimplement CAM_CAM mining, provider, corpus, or
self-enhancement behavior.

Rejected alternatives:

- A documentation-only skill would leave repeated users to assemble unsafe,
  inconsistent shell commands and would not create reliable receipts.
- Extending `cam_manager.py` to own directory discovery and mining would
  broaden the approval manager beyond its fixed-operation role. The manager is
  reused only for the existing supervised self-enhancement candidate boundary.

## Interface and Configuration

The coordinator accepts explicit paths for CAM runtime state and has portable
defaults only for the source directory:

```bash
python tools/cam_pull_mine_dir.py \
  --source-root /path/to/repos \
  --cam-command /path/to/CAM_CAM/.venv/bin/cam \
  --cam-db /path/to/CAM_CAM/claw.db \
  --cam-config /path/to/CAM_CAM/claw.toml \
  --profiles /path/to/CAM_CAM/model_profiles.toml \
  --wrapper /path/to/cam-codx \
  --state-dir /path/to/local_state/CAM_Codx/pull_mine_dir
```

`--source-root` defaults to the approved waswiki directory above. Other paths
must be explicit. Secrets are never accepted as CLI arguments or written to
reports.

A user-local, ignored configuration records an exact mining model and
conservative defaults for `max_repos`, `max_minutes`, and `max_cost_usd`. The
coordinator refuses a budgeted mining run unless the model and hard cap are
known. The user may override those values at invocation; no public repository
config is silently edited.

## Run Flow

1. Validate the source root, CAM executable, explicit database/config paths,
   local state directory, and model/budget settings. Record path fingerprints,
   not database contents or `.env` values.
2. Discover Git repositories beneath the source root without executing their
   code. For each repository, require a clean worktree, a non-detached branch,
   and an upstream. Run `fetch` followed by `pull --ff-only` only when those
   checks pass.
3. Skip and report dirty, conflicted, detached, no-upstream, unreachable, or
   non-fast-forward repositories. A skipped repository never blocks unrelated
   safe repositories from continuing.
4. Pin the selected `claw.db` in both CAM database environment variables and
   run `cam mine-workspace --changed-only --scan-only --no-tasks` against the
   source root. The scan output determines eligible candidates; it makes no
   model calls or corpus writes.
5. Invocation of the skill is explicit authorization for the bounded live
   mining step. Run the same selected scope through `cam mine-workspace` with
   `--changed-only`, `--no-tasks`, configured repository/time/cost limits, an
   exact model, and a durable budget receipt.
6. Compare pre/post corpus counts, SQLite integrity, mining ledger rows, run
   receipt state, eligible/mined/skipped repository lists, and recorded cost.
   CAM mining is expected to update the selected `claw.db`, mining registry,
   and receipt artifacts. It must not alter project repositories or emit CAM
   tasks.
7. Mark the result **meaningful** only when at least five new validated,
   provenance-bearing findings span at least two repositories and indicate a
   concrete repeated pattern or capability gap. Otherwise report the corpus
   update as useful but below the CAM-improvement threshold.
8. For a meaningful run, create a content-addressed manager packet and
   single-use receipt for exactly:

   ```text
   self-enhance start --mode supervised --max-tasks 1 --skip-swap
   ```

   The skill invocation is the recorded approval for that exact candidate run.
   The existing CAM self-enhancement pipeline must use its disposable candidate
   copy. No `swap`, `rollback`, model promotion, profile activation, live source
   edit, live configuration edit, or live corpus replacement is allowed.
9. Write Markdown and JSON reports with each phase's inputs, outcomes,
   candidate location, tests, and verdict. Retain failed candidates for review;
   never describe a failed candidate as a CAM update.

## Safety and Failure Rules

- Mining only occurs after the scan-only gate and only against the explicit
  primary database/configuration.
- Git updates are fast-forward only; no reset, merge, rebase, stash, branch
  switch, or forced operation is permitted.
- `--no-tasks` is mandatory for both scan and live mining.
- Failure of configuration, budget receipt, database integrity, or the live
  mining command stops later phases and records the exact failing phase.
- A meaningful result authorizes one bounded candidate test only. Candidate
  validation failure is a rejection, not a reason to retry or promote.
- A future live `self-enhance swap`, model action, or configuration change
  remains a separate explicit command and approval outside this skill.

## Report Contract

The report renders:

- source root and runtime fingerprints;
- updated, already-current, skipped, and failed repositories with reasons;
- scan-only candidate count and live mining selection;
- before/after methodology and ledger counts, SQLite integrity, run receipt,
  model, hard cap, and recorded cost;
- the meaningful-mining threshold result and evidence supporting it;
- candidate self-enhancement packet/receipt, candidate tests, and verdict when
  applicable;
- the exact separate next command if a reviewed promotion is ever desired.

Reports deliberately omit secrets, raw provider prompts, full database rows,
and private environment values.

## Verification Strategy

Tests use temporary Git repositories, fake `cam`/wrapper executables, fixture
scan/mine JSON, and temporary SQLite databases. They prove:

1. portable default and explicit source-root handling;
2. clean fast-forward updates versus skip-and-report behavior;
3. exact scan-only and live-mining argument lists, including `--no-tasks`;
4. database/ledger delta and integrity evidence rendering;
5. the five-findings/two-repositories/repeated-pattern threshold;
6. bounded candidate packet arguments and absence of swap/model/profile
   commands;
7. failure reporting and no later phase after a failed gate;
8. redaction of secrets and stable JSON/Markdown output.

No test may pull a real remote, call a provider, mine a live corpus, or start a
real self-enhancement run.

## Documentation and Installation

Add the `cam-codx-pull-mine-dir` template skill, include it in the setup wizard,
and document it in the README, CAM cheatsheet, program-manager guide, and CAM
mining documentation. The skill explains that invoking it authorizes its
bounded mining and candidate-test phases, but not a live CAM swap or model
promotion.
