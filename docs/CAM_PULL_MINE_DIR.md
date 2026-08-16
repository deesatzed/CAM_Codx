# CAM Pull Mine Directory

Use CAM_Codx to prepare an explicit pull/mine phase for an approved directory
of local repositories, one pinned CAM corpus, and a separately reviewed
no-swap candidate decision. It is not part of routine SWE work or read-only
assessment.

## What an invocation authorizes

The skill invocation authorizes one bounded cycle:

1. Inspect every nested Git repository without executing project code.
2. For clean attached repositories with an upstream, run only `git fetch
   origin` then `git pull --ff-only`.
3. Run CAM `mine-workspace --changed-only --no-tasks` against the exact pinned
   `claw.db` and `claw.toml`, first as a no-provider scan and then as a capped
   live pass.
4. Update that corpus, its normal `mining_registry.json` ledger, the CAM budget
   receipt, and private local Markdown/JSON reports.
5. If the evidence has at least five validated provenance-backed findings from
   at least two repositories and the operator attests a concrete repeated
   pattern or capability gap, create at most one manager-backed candidate:
   `self-enhance start --mode supervised --max-tasks 1 --skip-swap`.

It does not authorize `self-enhance swap`, model/profile promotion or rollback,
live configuration edits, force Git operations, or a retry of a rejected
candidate. Each needs a separate explicit approval and its own evidence.

## Source root and skips

The default source root is:

```text
/Volumes/WS4TB/waswiki/repos2mine/repo622sn
```

For another machine or user, pass `--source-root /absolute/path/to/repos`.
The coordinator reports and skips dirty, conflicted, detached, and no-upstream
repositories. A failed fetch or non-fast-forward pull is reported as failed and
does not stop the rest of the eligible directory.

## Setup

Install the skill with the normal CAM_Codx setup wizard:

```bash
cd /absolute/path/to/CAM_Codx
python tools/cam_setup_wizard.py \
  --cam-home ~/CAM \
  --skip-clone \
  --install-codex-skill \
  --non-interactive
```

Create a user-local defaults file from
`templates/config/cam-pull-mine-dir.example.toml`. It contains the exact model,
repository/time caps, and hard cost cap; it must not contain an API key.

## Preview first

Use `--dry-run` to validate paths, inspect Git eligibility, build the scan plan,
and write report paths without fetching, pulling, mining, changing `claw.db`,
updating the mining ledger, or issuing a candidate packet:

```bash
python /absolute/path/to/CAM_Codx/tools/cam_pull_mine_dir.py \
  --source-root /absolute/path/to/repos \
  --cam-command /absolute/path/to/cam \
  --cam-db /absolute/path/to/CAM_CAM/claw.db \
  --cam-config /absolute/path/to/CAM_CAM/claw.toml \
  --state-dir /absolute/path/to/local-state \
  --local-defaults /absolute/path/to/cam-pull-mine-dir.toml \
  --dry-run
```

Omit `--dry-run` only for the explicit bounded cycle. Add
`--repeated-pattern-or-gap` only after reviewing evidence that identifies the
concrete repeated pattern or capability gap; the coordinator otherwise reports
the evidence but does not start a candidate.

## Read the result

The command prints JSON and Markdown report paths. The reports record Git
updates/skips/failures, database/config fingerprints, integrity before and
after mining, corpus and ledger deltas, provenance-backed findings, the
meaningfulness decision, and the candidate verdict. They retain only digests
and bounded redacted command summaries; local report directories are mode 0700
and files are mode 0600.

## Verification scope

The shipped tests are fixture-only. They prove command construction, Git safety
boundaries, read-only SQLite snapshots, report redaction, manager invocation,
CLI parsing, and skill installation. They do not pull a remote repository,
mine a live corpus, contact a provider, or execute a self-enhancement
candidate.
