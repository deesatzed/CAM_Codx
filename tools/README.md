# tools/

Baseline-measurement harness and validation helpers for the Codex-CAM Methodology. None of these scripts is invoked automatically; each one is a prerequisite for a specific gated phase in [`../build_to_do_checklist.md`](../build_to_do_checklist.md) and is run by hand against real workspace data, per the validation gates in [`../docs/_validation_gates.md`](../docs/_validation_gates.md).

All scripts operate on real `codex` CLI output, real `claw.db` rows, and real SKILL.md files. None of them mock, stub, simulate, or cache anything; that policy is enforced workspace-wide and re-stated here so contributors do not loosen it locally.

---

## `baseline_cold_start.sh`

**Purpose.** Captures Codex CLI cold-start transcripts on a fixed set of unfamiliar repos, producing the "before" measurement that the Phase 9 COLD-START claim is compared against.

**Feeds gate.** Validation Gate 1.4 (cold-start transcripts captured on 5 unfamiliar real repos). Gate 9.4 (cold-start end-to-end claim) compares its "after" run against these transcripts.

**How to run.**

    bash tools/baseline_cold_start.sh --dry-run     # show what would run
    bash tools/baseline_cold_start.sh               # actually run
    bash tools/baseline_cold_start.sh --help        # print header

**Prerequisites.**

1. `baselines/manifest.json` exists and contains a `codex_cli_version` matching the live CLI (the script aborts on mismatch — Gate 1.2 falsifier).
2. `baselines/repo_set.txt` contains exactly 5 absolute repo paths, each on disk.
3. `prompts/orient_baseline.txt` exists and is non-empty.
4. `codex` is on `PATH`.

**Side effects.** Writes `baselines/cold_start/<repo_basename>.transcript.jsonl` and `<repo_basename>.timing.txt` per repo. Refuses to overwrite existing artifacts.

---

## `codex_trace_patterns.py`

**Purpose.** Centralizes the regex patterns used to classify events inside Codex CLI transcripts (tool calls, skill activations, user escalations, verification failures). Provides a `parse_transcript(path)` API and a CLI form that dumps the parsed structure as JSON.

**Feeds gates.** Gate 4.5 (Codex actually invokes `cam_recall`), Gate 5.2 (rescue ladder fires on 2nd consecutive failure), Gate 5.3 (rescue ladder does not over-trigger on 1st failure), Gate 6.3 (outcome_log writes after every verified recall), all Phase 9 behavioural gates.

**How to run.**

    python -m tools.codex_trace_patterns baselines/cold_start/<slug>.transcript.jsonl

Importing the module raises `RuntimeError` at import time if `baselines/manifest.json` is missing or has no `codex_cli_version` field. Parsing a transcript that declares a different CLI version than the manifest also raises — by design, to make version skew loud rather than silent.

**Version-tie.** Every regex in the module is version-tied to the Codex CLI version pinned in `baselines/manifest.json`. If the CLI is upgraded, every regex must be re-validated against fresh real transcripts before any gate that depends on it is trusted.

---

## `trigger_schema.json`

**Purpose.** JSON Schema (draft 2020-12) for the `auto_fire` frontmatter block in a Codex skill's `SKILL.md` file. Strict (`additionalProperties: false` at every level), with conditional `allOf` clauses that require the right sibling fields per `condition` value (`verbs_match` requires `verbs`; `consecutive_failures` requires `count` and `failure_kind`; etc.).

**Feeds gates.** Gate 4.1 (`cam_recall_and_cite` frontmatter parses), Gate 5.1 (`rescue_ladder` declares a parseable trigger), Cross-cutting Gate CC.5 (every auto-fire trigger validates).

**How to run.** Consumed by `validate_skill_frontmatter.py`; not used directly. Examples for each valid `condition` value are embedded inline.

---

## `validate_skill_frontmatter.py`

**Purpose.** Validates the `auto_fire` block of one or more `SKILL.md` files against `trigger_schema.json`. A SKILL.md without an `auto_fire` block is acceptable (skill simply does not auto-fire); a malformed `auto_fire` block is a hard failure.

**Feeds gates.** Gate 4.1, Gate 5.1, Cross-cutting Gate CC.5.

**How to run.**

    python tools/validate_skill_frontmatter.py path/to/SKILL.md
    python tools/validate_skill_frontmatter.py --dir /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills
    python tools/validate_skill_frontmatter.py --quiet path/to/SKILL.md   # exit code only
    python tools/validate_skill_frontmatter.py --verbose --dir /path      # print every file

**Exit codes.** `0` if every inspected file validates (or has no `auto_fire` block). `1` if any file's `auto_fire` block is malformed. `2` on usage error. `3` if PyYAML or jsonschema is not installed.

**Dependencies.** PyYAML and jsonschema. The script prints an actionable `pip install` message if either is missing; it does not silently fall back to a regex parser.

---

## Conventions all scripts follow

- **Real data only.** No mock, no stub, no simulation, no cached response, no placeholder, no demo. Every script aborts rather than fabricate.
- **No automatic execution.** These scripts are invoked manually as part of the gated checklist; nothing runs them on a schedule or on commit.
- **Absolute paths everywhere.** Scripts derive their own location and walk up to the repo root; they do not depend on the caller's `cwd`.
- **Loud failure on drift.** Version mismatches (manifest vs live CLI, manifest vs transcript header) raise rather than degrade gracefully. The gates depend on the contract being identical; degradation would silently invalidate later behavioural claims.
- **Heavy comments where the rationale is not obvious.** Every non-trivial branch has a short comment explaining the why; the code is meant to be read and audited.
