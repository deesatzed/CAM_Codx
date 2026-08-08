# CAM Model Benchmark Implementation Baseline

Date: 2026-08-08

## Scope

This receipt starts implementation of the approved CAM mining-model comparison. It records checkout, runtime, credential-presence, and focused-test truth before benchmark code or paid model calls.

## Checkouts

- CAM_Codx implementation worktree: `/Volumes/WS4TB/repo622sn/.worktrees/CAM_Codx-model-benchmark`
- CAM_Codx branch/HEAD: `codex/cam-model-benchmark-manager` at `c12fa4dff402ce0e6946993a01bed8125683d72b`
- CAM_CAM live checkout: `/Volumes/WS4TB/repo622sn/CAM_CAM` at `db5495a5b963688a9c29e5d06c5447e781544f1c`
- CAM_CAM implementation worktree: `/Volumes/WS4TB/repo622sn/.worktrees/CAM_CAM-model-benchmark`
- CAM_CAM implementation branch/HEAD: `codex/cam-model-benchmark-runtime` at `db5495a5b963688a9c29e5d06c5447e781544f1c`

The live CAM_CAM checkout had pre-existing changes and was not edited:

```text
 M claw.toml
?? claw.db-shm
?? claw.db-wal
```

## Runtime and credential preflight

- Python: `3.13.9`
- Installed `cam`: `/Users/o2satz/miniforge3/envs/py313/bin/cam`
- Installed `claw` module: `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/__init__.py`
- Intended live configuration: `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.toml`
- Intended authoritative corpus: `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db`
- Intended environment file: `/Volumes/WS4TB/repo622sn/CAM_CAM/.env`
- `OPENROUTER_API_KEY`: present by name only
- `.env`: ignored by Git
- Codex authentication: `Logged in using ChatGPT`

The installed `cam`/`claw` provenance does not match the implementation checkout. All development and benchmark commands must therefore use the clean worktree explicitly through `PYTHONPATH=src python -m claw.cli` or an equivalent worktree-local environment.

## Focused baseline test

Command:

```bash
python -m pytest -q tests/test_config.py tests/test_llm.py tests/test_openrouter.py \
  tests/test_miner.py tests/test_mining_enhancements.py tests/test_cli_ux.py
```

Result: `286 passed, 1 failed` in 8.98 seconds.

The existing failure is:

```text
tests/test_config.py::TestLoadConfig::test_loads_claw_toml
expected database.db_path == "data/claw.db"
actual database.db_path == "claw.db"
```

This mismatch exists at the clean source commit and is recorded as a pre-existing baseline failure. It does not prevent test-first implementation of the isolated model catalog and profile surfaces. It must remain visible in regression reports and must not be relabeled as introduced by this branch.

## Spend and mutation status

- OpenRouter benchmark calls made: `0`
- Recorded OpenRouter benchmark spend: `$0.00`
- Codex comparison credits used: `0`
- Model profile promotions: `0`
- Live corpus writes: `0`

