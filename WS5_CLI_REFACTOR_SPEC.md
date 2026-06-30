# WS5 — CLI Surface Contraction Spec

**Status:** SPEC (ready to implement on approval). Engine change → lands in
`deesatzed/CAM_CAM` on a branch, behind back-compat aliases.
**Source:** `CAM_CLI_ASSESSMENT.md`. Implements `GOAL_CAM_HYGIENE.md` WS5.

## Principle
Group by noun; keep a small set of high-frequency verbs at top level. **Keep every
existing command working** via hidden deprecated aliases for one release, so this is
not a hard break.

## Target top-level (13 verbs + groups)
```
init · evaluate · enhance · create · validate · mine · enrich · learn · kb · doctor · pulse · mcp · dashboard
groups: task · forge · security · cag · self-enhance   (research hidden behind --experimental)
```

## Command mapping (old → new)

| Old | New | Action |
|---|---|---|
| `mine` | `mine` | keep (default) |
| `mine-workspace` | `mine workspace` | move into `mine` group; alias `mine-workspace` hidden+deprecated |
| `mine-all` | `mine all` | move; hidden alias |
| `mine-self` | `mine self` | move; hidden alias |
| `mine-report` | `mine report` | move; already hidden |
| `premine` | `mine premine` | move; keep `premine` as visible alias (distinct enough) |
| `status` | `doctor status` | already exists as `doctor status`; drop top-level `status` (hidden alias) |
| `stats` | `kb stats` | add under `kb`; hidden alias `stats` |
| `gaps` | `kb gaps` | add under `kb`; hidden alias `gaps` |
| `benchmark` | `forge benchmark` | drop top-level dup; hidden alias |
| `federate` | `kb federate` | move into `kb` (cross-ganglion query); hidden alias |
| hidden `add-goal`,`keycheck`,`reassess`,`assimilation-report/-delta`,`forge-export/-benchmark`,`prism-demo` | (group form only) | remove top-level registration; keep ONLY the grouped command |
| `chat`,`ab-test`,`evolution` | `--experimental`-gated | hide unless `CAM_EXPERIMENTAL=1` or `--experimental`, pending usage confirmation |

## Cross-cutting fixes
1. **`--config` everywhere:** add `--config/-c` to every corpus-touching command
   (currently missing on some `kb`/`security`/`cag`/`learn` subcommands — audit each).
2. **De-dup hidden+grouped:** for each grouped alias whose target is a hidden top-level
   command, delete the hidden top-level `@app.command` and point the group command at the
   underlying async fn directly.
3. **`evaluate` vs `camify`:** document the distinction in both help strings, or merge
   `camify` into `evaluate --plan`. (Decision needed.)
4. **`preflight` wording:** remove "estimate time/budget" from its help/behavior — conflicts
   with the standing no-time/cost-estimate rule. Replace with "scope and clarify the task."

## Implementation steps (Typer)
1. Branch `feat/cli-contraction` off `CAM_CAM` main.
2. For each move: register the command under its group `Typer` app; replace the top-level
   `@app.command` with a hidden alias that calls the same fn (or delete if already hidden).
3. Add `--config` params where missing; thread to `load_config`.
4. Add `--experimental` gate (callback that hides commands unless env/flag set).
5. Update `cli/__init__.py` docstring + any `COMMANDS_INDEX`.
6. Tests: assert every OLD invocation still resolves (back-compat) and every NEW path works.
7. Update help snapshot tests.

## Definition of done
- `cam --help` shows the 13-verb contracted surface.
- Every pre-existing command still runs (hidden alias) with a deprecation note.
- `--config` accepted by all corpus commands.
- `preflight` no longer references time/budget estimates.
