---
name: cam-codx-pull-mine-dir
description: Safely update eligible Git repositories, mine one pinned CAM corpus, and assess whether the resulting evidence warrants one supervised no-swap CAM candidate. Use when a developer explicitly asks CAM_Codx to pull and mine a repository directory, including an alternate user-owned source root.
---

# CAM Pull Mine Directory

Run this skill only for an explicit pull-and-mine request. Invocation authorizes
the coordinator's bounded mining cycle; it does not authorize a swap, model or
profile change, rollback, live configuration edit, or unrestricted provider use.

## Resolve the scope

1. Resolve the installed `CAM_Codx` tool, CAM command, corpus database,
   `claw.toml`, local state directory, and optional model-profiles file. Never
   print `.env` contents, API keys, or raw database content.
2. Use `/Volumes/WS4TB/waswiki/repos2mine/repo622sn` only when it exists and
   the user did not name another root. Otherwise require `--source-root` with
   the user-owned directory.
3. Read a user-local defaults TOML for the exact model, repository/time caps,
   and hard cost cap. Do not put credentials or a model budget in the skill,
   command history, or Git.
4. State the resolved source root, pinned corpus/config paths, limits, and
   whether the request is `--dry-run` or a live bounded cycle.

## Run the coordinator

Use list-form arguments through the installed coordinator. Substitute only
resolved absolute paths:

```bash
python /absolute/path/to/CAM_Codx/tools/cam_pull_mine_dir.py \
  --source-root /absolute/path/to/repos \
  --cam-command /absolute/path/to/cam \
  --cam-db /absolute/path/to/claw.db \
  --cam-config /absolute/path/to/claw.toml \
  --state-dir /absolute/path/to/local-state \
  --local-defaults /absolute/path/to/cam-pull-mine-dir.toml
```

Use `--dry-run` only when the developer requests a preview. It validates paths,
discovers repositories, and inspects Git eligibility, but never fetches, pulls,
mines, writes the corpus/ledger, or creates a manager packet.

Without `--dry-run`, the coordinator may only:

- skip dirty, conflicted, detached, no-upstream, or non-fast-forward repos;
- update eligible repos through `git fetch origin` and `git pull --ff-only`;
- run a scan before the capped `mine-workspace --changed-only --no-tasks` pass;
- update the pinned corpus, normal mining ledger, and local redacted receipts;
- dispatch at most one manager-backed `self-enhance start --mode supervised
  --max-tasks 1 --skip-swap` candidate after all meaningfulness gates pass.

## Interpret and report

Return the JSON and Markdown report paths plus a compact summary of repository
updates/skips/failures, database integrity, corpus and ledger delta,
provenance-backed findings, meaningfulness verdict, and candidate verdict.

Treat a `candidate_completed_no_swap` result as a completed isolated run, not
as promotion or proof of an accepted improvement. A nonzero candidate result is
`candidate_rejected`; do not retry it automatically.

Never issue `self-enhance swap`, `models set`, `models rollback`, `models
profile use`, `--force`, shell commands, or a live configuration change from
this skill. Those require a distinct explicit CAM command and approval.
