# Pull, Mine, and Review CAM Skill Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Build the installable `cam-codx-pull-mine-dir` skill and a deterministic
CAM_Codx coordinator that updates eligible Git repositories, mines one explicit
CAM corpus, assesses the resulting evidence, and optionally runs one
supervised no-swap CAM candidate test.

**Architecture:** Keep orchestration in `tools/cam_pull_mine_dir.py`. The tool
uses list-form subprocess calls, pins the database environment, delegates
mining/self-enhancement to CAM_CAM, and writes redacted JSON/Markdown receipts.
It reuses `tools/cam_manager.py` only for the already-allowlisted
`self-enhance-start` candidate boundary; it never implements CAM runtime logic.

**Tech Stack:** Python 3.13 standard library, SQLite read-only/integrity
queries, Git CLI, CAM_CAM `mine-workspace`, CAM_Codx manager, pytest, Codex
skill templates.

---

## Task 0: Record the recalled-methodology decision before implementation

**Files:**
- Create: `IMPLEMENT.md`
- Modify: `DECISIONS.md`

**Step 1: Retrieve candidate CAM methodologies**

Use `cam_recall_and_cite` with the implementation step description “bounded
directory Git update, corpus mining, and supervised candidate self-improvement
orchestration.” Request provenance for every methodology that may influence the
tool design.

**Step 2: Record the selected and rejected patterns**

Create `IMPLEMENT.md` using the exact block required by `cam_recall_and_cite`.
Record an explicit application note for each selected pattern. If no applicable
methodology is available, record that fact rather than inventing one.

**Step 3: Record the new boundary decision**

Add a dated `DECISIONS.md` entry: this skill’s invocation is the user’s
authorization for its bounded mining and candidate-test phase, but never for a
swap, model/profile change, or live configuration change.

**Step 4: Verify the documentation surface**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

**Step 5: Commit**

```bash
git add IMPLEMENT.md DECISIONS.md
git commit -m "docs: record pull mine skill methodology boundary"
```

## Task 1: Add typed configuration, receipts, and assessment contracts

**Files:**
- Create: `tools/cam_pull_mine_dir.py`
- Create: `tests/test_cam_pull_mine_dir.py`
- Create: `templates/config/cam-pull-mine-dir.example.toml`

**Step 1: Write failing contract tests**

Create tests for:

- default source root
  `/Volumes/WS4TB/waswiki/repos2mine/repo622sn`;
- an explicit `--source-root` overriding the default;
- rejecting a missing path, missing executable, non-positive limits, and a
  budget without an exact model;
- a `MeaningfulAssessment` being positive only for five or more validated,
  provenance-bearing findings across two or more repositories plus a repeated
  pattern or capability gap.

Use only temporary paths and pure objects. The first test should expect an
import failure because the module does not yet exist.

**Step 2: Run the new tests to prove they fail**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py
```

Expected: collection/import failure for `tools.cam_pull_mine_dir`.

**Step 3: Implement the smallest typed contract**

Add these public types and pure helpers:

```python
DEFAULT_SOURCE_ROOT = Path("/Volumes/WS4TB/waswiki/repos2mine/repo622sn")

@dataclass(frozen=True)
class PullMineConfig:
    source_root: Path
    cam_command: Path
    cam_db: Path
    cam_config: Path
    profiles: Path | None
    wrapper: Path | None
    state_dir: Path
    exact_model: str | None
    max_repos: int
    max_minutes: int
    max_cost_usd: float | None

@dataclass(frozen=True)
class CorpusSnapshot:
    methodology_count: int
    ledger_entries: int
    integrity: str

@dataclass(frozen=True)
class MeaningfulAssessment:
    is_meaningful: bool
    findings: int
    source_repositories: int
    repeated_pattern_or_gap: bool
    reasons: tuple[str, ...]
```

Implement `load_local_defaults()`, `validate_config()`,
`assess_meaningful_mining()`, and JSON-safe `to_dict()` methods. Read the
optional user-local TOML from an explicit argument; do not look up secrets or
modify `claw.toml`.

The example TOML must contain placeholders only:

```toml
exact_model = "replace-with-your-approved-model"
max_repos = 20
max_minutes = 120
max_cost_usd = 5.0
```

**Step 4: Run the focused tests**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py
```

Expected: all Task 1 tests pass.

**Step 5: Commit**

```bash
git add tools/cam_pull_mine_dir.py tests/test_cam_pull_mine_dir.py templates/config/cam-pull-mine-dir.example.toml
git commit -m "feat: add pull mine directory contracts"
```

## Task 2: Discover repositories and perform safe fast-forward updates

**Files:**
- Modify: `tools/cam_pull_mine_dir.py`
- Modify: `tests/test_cam_pull_mine_dir.py`

**Step 1: Write failing Git-boundary tests**

Add a fake command runner that records list-form argv and returns configured
stdout/stderr/exit status. Cover:

- discovering nested directories containing `.git` without executing project
  code;
- a clean, attached, upstream-tracking repository receiving only `git fetch
  origin` then `git pull --ff-only`;
- dirty, detached, no-upstream, fetch-failed, and non-fast-forward repositories
  becoming `skipped` or `failed` receipt rows;
- one bad repository not preventing a later clean repository from updating;
- no `reset`, `merge`, `rebase`, `stash`, `checkout`, `switch`, or force flag.

**Step 2: Run the focused failure set**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k git
```

Expected: failures for missing discovery/update functions.

**Step 3: Implement list-form Git operations**

Introduce:

```python
@dataclass(frozen=True)
class RepositoryUpdate:
    path: Path
    branch: str | None
    status: Literal["updated", "already_current", "skipped", "failed"]
    reason: str

def discover_git_repositories(root: Path) -> tuple[Path, ...]: ...
def inspect_update_eligibility(repo: Path, runner: CommandRunner) -> Eligibility: ...
def update_repository(repo: Path, runner: CommandRunner) -> RepositoryUpdate: ...
```

Use `git -C <repo> status --porcelain=v1 --branch`, `git -C <repo> rev-parse
--abbrev-ref HEAD`, `git -C <repo> rev-parse --abbrev-ref @{upstream}`, then
`fetch origin` and `pull --ff-only`. Pass no shell string and do not write in a
project repository outside Git’s normal fast-forward update.

**Step 4: Run the Git-focused tests**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k git
```

Expected: all Git-boundary tests pass.

**Step 5: Commit**

```bash
git add tools/cam_pull_mine_dir.py tests/test_cam_pull_mine_dir.py
git commit -m "feat: update eligible repositories before mining"
```

## Task 3: Pin the corpus and construct scan/live mining commands

**Files:**
- Modify: `tools/cam_pull_mine_dir.py`
- Modify: `tests/test_cam_pull_mine_dir.py`

**Step 1: Write failing CAM command tests**

Add tests that assert the scan argv is exactly:

```text
<cam> mine-workspace <source-root> --target <source-root> --changed-only --scan-only --no-tasks --max-repos <N> --max-minutes <N> --config <config>
```

Assert the live argv removes only `--scan-only`, adds `--no-tasks`, the
configured `--profiles` when supplied, and the all-or-nothing triple
`--max-cost-usd`, `--exact-model`, `--budget-receipt`. Assert the child
environment pins both `CLAW_DB_PATH` and `CAM_CODEX_MCP_DB_PATH` to the exact
database path while preserving other environment variables.

Add tests proving a failed scan prevents live mining and a live run never adds
task-generation, `--fast`, or `--self-assess` flags.

**Step 2: Run the command tests to prove they fail**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k mining_command
```

Expected: failures for missing command builders or environment pinning.

**Step 3: Implement command construction and controlled execution**

Add:

```python
def build_scan_argv(config: PullMineConfig) -> list[str]: ...
def build_live_argv(config: PullMineConfig, receipt_path: Path) -> list[str]: ...
def pinned_cam_environment(config: PullMineConfig) -> dict[str, str]: ...
```

Use `subprocess.run(argv, cwd=config.cam_command.parent.parent, env=..., shell=False,
capture_output=True, text=True, check=False)`. Store only stdout/stderr digests
and bounded summaries in the receipt, never raw provider output or environment
values. Require a valid exact model and hard cap for the live command.

**Step 4: Run the command tests**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k mining_command
```

Expected: all command-boundary tests pass.

**Step 5: Commit**

```bash
git add tools/cam_pull_mine_dir.py tests/test_cam_pull_mine_dir.py
git commit -m "feat: pin bounded workspace mining commands"
```

## Task 4: Measure corpus deltas and render durable reports

**Files:**
- Modify: `tools/cam_pull_mine_dir.py`
- Modify: `tests/test_cam_pull_mine_dir.py`

**Step 1: Write failing evidence/report tests**

Use temporary SQLite databases containing only the minimum `methodologies` and
mining-ledger fixture data. Test:

- `PRAGMA integrity_check` must be `ok` before and after mining;
- counts and source-repository sets create a truthful delta;
- five findings from one repository is below the meaningful threshold;
- five findings from two repositories without a repeated pattern/gap is below
  the threshold;
- five findings from two repositories with a repeated pattern/gap is positive;
- Markdown and JSON reports list updates/skips/failures and redact a sentinel
  secret value.

**Step 2: Run the report tests to prove they fail**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k 'snapshot or meaningful or report'
```

Expected: failures for missing snapshot/report functions.

**Step 3: Implement read-only evidence helpers and report writers**

Implement SQLite access using a read-only URI and `PRAGMA query_only=ON`.
Support the actual authoritative methodology table schema by validating expected
columns before querying. Read the mining registry/ledger as JSON only when it
exists; otherwise render `ledger unavailable`, not a fabricated count.

Add:

```python
def snapshot_corpus(db: Path, ledger_path: Path | None) -> CorpusSnapshot: ...
def derive_mining_delta(before: CorpusSnapshot, after: CorpusSnapshot, ...): ...
def render_markdown_report(receipt: PullMineReceipt) -> str: ...
def write_report(receipt: PullMineReceipt, output_dir: Path) -> tuple[Path, Path]: ...
```

Create output directories at mode `0700` and JSON/Markdown receipt files at
mode `0600`.

**Step 4: Run the evidence/report tests**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k 'snapshot or meaningful or report'
```

Expected: all evidence and report tests pass.

**Step 5: Commit**

```bash
git add tools/cam_pull_mine_dir.py tests/test_cam_pull_mine_dir.py
git commit -m "feat: report corpus deltas and mining meaning"
```

## Task 5: Launch only the bounded no-swap candidate when warranted

**Files:**
- Modify: `tools/cam_pull_mine_dir.py`
- Modify: `tests/test_cam_pull_mine_dir.py`
- Reference: `tools/cam_manager.py:193-289`

**Step 1: Write failing candidate-boundary tests**

Mock `prepare_packet`, `issue_approval`, and `execute_packet`. Test that a
meaningful receipt calls them in order with:

```python
operation="self-enhance-start"
args=["--mode", "supervised", "--max-tasks", "1", "--skip-swap"]
approved_by="cam-codx-pull-mine-dir invocation"
```

Assert non-meaningful and failed mining runs never call the manager. Assert no
argument contains `swap`, `rollback`, `models`, `profile`, `--force`, or a
secret marker. Assert candidate test failure becomes `candidate_rejected` and
does not cause a retry.

**Step 2: Run the candidate tests to prove they fail**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k candidate
```

Expected: failures for the missing candidate dispatcher.

**Step 3: Implement the manager-backed candidate dispatcher**

Import only the public manager functions. Create a unique workflow ID from the
receipt digest, pass the caller-supplied wrapper and local state directory, and
place the single-use approval in the existing secured manager state. Record the
packet path, approval path, receipt path, return code, and candidate verdict in
the Pull/Mine receipt. Do not parse or reproduce raw manager output.

**Step 4: Run candidate and manager regression tests**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py -k candidate
python -m pytest -q tests/test_cam_manager.py
```

Expected: all tests pass and the existing manager’s single-use approval tests
remain unchanged.

**Step 5: Commit**

```bash
git add tools/cam_pull_mine_dir.py tests/test_cam_pull_mine_dir.py
git commit -m "feat: run bounded CAM improvement candidates"
```

## Task 6: Add the CLI, installable skill, and setup integration

**Files:**
- Modify: `tools/cam_pull_mine_dir.py`
- Create: `templates/skills/cam-codx-pull-mine-dir/SKILL.md`
- Create: `templates/skills/cam-codx-pull-mine-dir/agents/openai.yaml`
- Modify: `tools/cam_setup_wizard.py:345-364`
- Modify: `tests/test_cam_setup_wizard.py`
- Modify: `tests/test_cam_pull_mine_dir.py`

**Step 1: Write failing CLI and installation tests**

Add tests for `--help`, default source-root rendering, explicit argument
validation, `--dry-run` stopping before Git/CAM writes, and JSON report paths.
Extend the setup test’s expected installed skill set with
`cam-codx-pull-mine-dir`.

**Step 2: Run the failing tests**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py tests/test_cam_setup_wizard.py
```

Expected: failures for the CLI parser and absent template skill.

**Step 3: Implement the CLI parser and skill template**

Add a CLI that accepts explicit CAM paths and optional source-root/model/limits
overrides. Make `--dry-run` perform validation, Git eligibility inspection, and
scan-only planning only; it must not fetch, pull, mine, or issue a candidate
packet.

Initialize the template with the skill-creator initializer:

```bash
python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  cam-codx-pull-mine-dir \
  --path templates/skills \
  --interface display_name="CAM Pull Mine Directory" \
  --interface short_description="Update repositories, mine one corpus, and assess CAM improvement evidence." \
  --interface default_prompt="Use CAM_Codx_Pull_Mine_Dir to update and mine this repository directory."
```

Replace its generated body with concise imperative instructions: resolve exact
paths, show the run scope, invoke the coordinator, surface the JSON/Markdown
report, and never issue a live swap/model command. Add the template name to
`install_codex_skills()`.

**Step 4: Run focused verification**

Run:

```bash
python -m pytest -q tests/test_cam_pull_mine_dir.py tests/test_cam_setup_wizard.py
python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py templates/skills/cam-codx-pull-mine-dir
```

Expected: tests pass and the validator prints `Skill is valid!`.

**Step 5: Commit**

```bash
git add tools/cam_pull_mine_dir.py templates/skills/cam-codx-pull-mine-dir tools/cam_setup_wizard.py tests/test_cam_setup_wizard.py tests/test_cam_pull_mine_dir.py
git commit -m "feat: install pull mine directory skill"
```

## Task 7: Document the feature and complete release verification

**Files:**
- Create: `docs/CAM_PULL_MINE_DIR.md`
- Modify: `README.md`
- Modify: `docs/CAM_CHEATSHEET.md`
- Modify: `docs/CAM_CODEX_PROGRAM_MANAGER.md`
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md`

**Step 1: Write documentation acceptance tests/checks**

Add assertions in `tests/test_cam_pull_mine_dir.py` that the generated report
contains the source-root override, skip reasons, database/config fingerprints,
threshold verdict, candidate verdict, and no secret sentinel. Do not add a
test that calls a real remote or provider.

**Step 2: Write the operator documentation**

Document:

- the default root and `--source-root` override;
- exactly which Git repositories are skipped and why;
- that invocation authorizes bounded mining, `claw.db`/ledger/receipt updates,
  and at most one no-swap candidate test;
- that swaps, model/profile changes, and config changes require a separate
  command and approval;
- a setup example and `--dry-run` example using placeholders only;
- fixture-only verification limits.

**Step 3: Run the complete local verification gate**

Run:

```bash
python -m pytest -q -p no:cacheprovider tests
python tools/generate_agent_packs.py --check
python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py templates/skills/cam-codx-pull-mine-dir
git diff --check
git status --short --branch
```

Expected: all tests pass, generated packs are current, the skill validates,
the diff has no whitespace errors, and no unplanned changes are staged.

**Step 4: Record truthful results**

Update `PROGRESS.md` with actual command outputs, commit IDs, the fixture-only
test limitation, and any unavailable local runtime preconditions. Update
`DECISIONS.md` if implementation changes an approved boundary.

**Step 5: Commit**

```bash
git add docs/CAM_PULL_MINE_DIR.md README.md docs/CAM_CHEATSHEET.md docs/CAM_CODEX_PROGRAM_MANAGER.md PROGRESS.md DECISIONS.md tests/test_cam_pull_mine_dir.py
git commit -m "docs: explain pull mine directory workflow"
```

## Final Integration Checklist

1. Review every commit in `plan/cam-pull-mine-dir` against
   `docs/plans/2026-08-11-pull-mine-dir-skill-design.md`.
2. Verify no code invokes `self-enhance swap`, `models set`, `models rollback`,
   or `models profile use`.
3. Verify no real Git remote, provider, live corpus, or self-enhancement run
   was invoked by tests.
4. Merge only after an explicit user decision, then rerun Task 7’s complete
   gate from the merged `main` checkout.
