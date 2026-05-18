#!/usr/bin/env bash
# =============================================================================
# baseline_cold_start.sh
# -----------------------------------------------------------------------------
# Captures cold-start Codex CLI transcripts on a fixed set of unfamiliar repos.
# Feeds Validation Gate 1.4 in docs/_validation_gates.md, and is the prerequisite
# baseline for the Phase 9 COLD-START claim (Gate 9.4).
#
# Why this script exists:
#   The Phase 9 cold-start claim measures a DELTA. Without a frozen, real
#   transcript captured against the unmodified Codex CLI + unmodified corpus,
#   the later "after" run has nothing to be compared against. Per workspace
#   policy any unfalsifiable claim is a dropped claim, so the baseline must
#   exist before any methodology code lands.
#
# What it does:
#   1. Reads baselines/repo_set.txt (one absolute repo path per line; # = comment)
#   2. For each repo:
#        a. Runs `codex exec --skip-git-repo-check` with the fixed orientation
#           prompt at prompts/orient_baseline.txt against the repo's cwd.
#        b. Tees stdout/stderr to baselines/cold_start/<basename>.transcript.jsonl
#        c. Captures wall-clock + RSS via /usr/bin/time -l into
#           baselines/cold_start/<basename>.timing.txt
#   3. Refuses to run if baselines/manifest.json is missing (Gate 1.2 pin).
#   4. Refuses to run if the live `codex --version` does not match the version
#      pinned in baselines/manifest.json (codex_cli_version field).
#   5. Exits 0 only if every repo produced a non-empty transcript AND a
#      non-empty timing file.
#
# What it does NOT do:
#   - It does NOT stub, mock, or simulate `codex`. The real CLI must be on PATH.
#   - It does NOT modify the repos under test (read-only orientation prompt).
#   - It does NOT populate manifest.json on its own — the human runs the pin
#     step in Phase 1 Step 1.1 first, against their real machine.
#
# Flags:
#   --dry-run   Print the codex commands that would run; do not execute.
#   --help      Print this header and exit 0.
#
# Real-data requirement:
#   Real `codex` binary on PATH. Real third-party repos on disk. No fakes.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Resolve script + repo-root paths up front so every later reference is absolute.
# -----------------------------------------------------------------------------
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "${SCRIPT_PATH}")"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

REPO_SET_FILE="${REPO_ROOT}/baselines/repo_set.txt"
PROMPT_FILE="${REPO_ROOT}/prompts/orient_baseline.txt"
MANIFEST_FILE="${REPO_ROOT}/baselines/manifest.json"
OUT_DIR="${REPO_ROOT}/baselines/cold_start"

DRY_RUN=0

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
print_help() {
  # Print the header comment block of this script (lines starting with "# ").
  # Using sed once on the script itself; no clever tricks beyond that.
  sed -n '2,/^# ===/p' "${SCRIPT_PATH}" | sed -e 's/^# \{0,1\}//'
}

die() {
  # Write an error line to stderr and exit non-zero. The message describes
  # what failed so the human running the harness gets an actionable signal.
  printf 'baseline_cold_start.sh: ERROR: %s\n' "$*" >&2
  exit 2
}

# -----------------------------------------------------------------------------
# Parse args
# -----------------------------------------------------------------------------
for arg in "$@"; do
  case "$arg" in
    --help|-h)
      print_help
      exit 0
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      die "unknown argument: ${arg} (use --help)"
      ;;
  esac
done

# -----------------------------------------------------------------------------
# Pre-flight: required inputs must exist as real files.
# These checks correspond to validation-gate prerequisites:
#   - manifest.json   → Gate 1.2 (CLI + model pinned)
#   - repo_set.txt    → Gate 1.4 (5 unfamiliar repos selected)
#   - prompt file     → fixed orientation prompt, kept under version control
# -----------------------------------------------------------------------------
[[ -f "${MANIFEST_FILE}" ]] \
  || die "baselines/manifest.json not found at ${MANIFEST_FILE}. Run Phase 1 Step 1.1 first (populate from baselines/manifest.json.template against the real machine)."

[[ -f "${REPO_SET_FILE}" ]] \
  || die "baselines/repo_set.txt not found at ${REPO_SET_FILE}."

[[ -f "${PROMPT_FILE}" ]] \
  || die "prompts/orient_baseline.txt not found at ${PROMPT_FILE}."

# -----------------------------------------------------------------------------
# `codex` must be on PATH. We will not silently fall back to anything else.
# -----------------------------------------------------------------------------
command -v codex >/dev/null 2>&1 \
  || die "codex CLI not found on PATH. This harness uses the real CLI only; no stub is acceptable."

# -----------------------------------------------------------------------------
# Version match check (Gate 1.2 falsifier guard).
# -----------------------------------------------------------------------------
# Read the pinned version out of the manifest. We use python3 with the stdlib
# json module to avoid taking a dependency on jq just for one field. python3
# is required elsewhere in this build (CAM_CAM requires >=3.12) so this is safe.
PINNED_VERSION="$(python3 -c '
import json, pathlib, sys
m = json.loads(pathlib.Path(sys.argv[1]).read_text())
v = m.get("codex_cli_version", "")
if not v:
    sys.stderr.write("manifest.json is missing codex_cli_version\n")
    sys.exit(3)
print(v)
' "${MANIFEST_FILE}")" || die "could not read codex_cli_version from manifest.json"

# `codex --version` is the canonical, machine-readable identity of the CLI.
# We compare verbatim. Any drift means the recorded baseline no longer applies.
LIVE_VERSION="$(codex --version 2>/dev/null || true)"
[[ -n "${LIVE_VERSION}" ]] \
  || die "\`codex --version\` produced no output."

if [[ "${LIVE_VERSION}" != *"${PINNED_VERSION}"* && "${PINNED_VERSION}" != *"${LIVE_VERSION}"* ]]; then
  die "codex CLI version drift. manifest pinned='${PINNED_VERSION}' live='${LIVE_VERSION}'. Re-pin the manifest or revert the CLI; do not silently proceed (Gate 1.2 falsifier)."
fi

# -----------------------------------------------------------------------------
# Load the fixed orientation prompt once. It is read from disk every run so
# any drift is captured by git; the script does not embed it.
# -----------------------------------------------------------------------------
PROMPT_TEXT="$(cat "${PROMPT_FILE}")"
[[ -n "${PROMPT_TEXT}" ]] || die "prompts/orient_baseline.txt is empty."

# -----------------------------------------------------------------------------
# Parse the repo set. Comments (#) and blank lines are ignored. Every other
# line must be an absolute path to an existing directory.
# -----------------------------------------------------------------------------
mapfile -t RAW_LINES < "${REPO_SET_FILE}"
REPOS=()
for line in "${RAW_LINES[@]}"; do
  # Trim leading/trailing whitespace.
  trimmed="${line#"${line%%[![:space:]]*}"}"
  trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
  # Skip blank lines and comment lines.
  [[ -z "${trimmed}" ]] && continue
  [[ "${trimmed:0:1}" == "#" ]] && continue
  REPOS+=("${trimmed}")
done

# Hard requirement: Gate 1.4 demands exactly 5 unfamiliar repos. Anything less
# would silently weaken the baseline. Anything more would expand scope without
# checklist approval.
if [[ "${#REPOS[@]}" -ne 5 ]]; then
  die "baselines/repo_set.txt must contain exactly 5 active (non-commented) repo paths; found ${#REPOS[@]}. Phase 1 Step 1.4 cannot proceed otherwise."
fi

# Every path must be an absolute directory on disk. No invention.
for repo in "${REPOS[@]}"; do
  [[ "${repo:0:1}" == "/" ]] \
    || die "repo path is not absolute: ${repo}"
  [[ -d "${repo}" ]] \
    || die "repo path does not exist on disk: ${repo} (do not fabricate; resolve before running)"
done

# -----------------------------------------------------------------------------
# Output directory. Created if missing. We do NOT clobber existing transcripts;
# the harness refuses to overwrite a prior baseline run so the human notices.
# -----------------------------------------------------------------------------
mkdir -p "${OUT_DIR}"

# -----------------------------------------------------------------------------
# Dry-run path: print what we WOULD do, exit clean. No `codex` invocation.
# -----------------------------------------------------------------------------
if [[ "${DRY_RUN}" -eq 1 ]]; then
  printf 'DRY RUN — no commands will execute.\n'
  printf 'Pinned codex version: %s\n' "${PINNED_VERSION}"
  printf 'Live codex version:   %s\n' "${LIVE_VERSION}"
  printf 'Output directory:     %s\n' "${OUT_DIR}"
  printf 'Repos to be exercised (%d):\n' "${#REPOS[@]}"
  for repo in "${REPOS[@]}"; do
    slug="$(basename "${repo}")"
    printf '  - repo:       %s\n' "${repo}"
    printf '    transcript: %s/%s.transcript.jsonl\n' "${OUT_DIR}" "${slug}"
    printf '    timing:     %s/%s.timing.txt\n' "${OUT_DIR}" "${slug}"
    printf '    command:    codex exec --skip-git-repo-check --cwd %q <orient_baseline.txt>\n' "${repo}"
  done
  exit 0
fi

# -----------------------------------------------------------------------------
# Real run loop. One repo at a time, sequentially — interleaved runs would
# confound the per-repo RSS / wall-clock numbers.
# -----------------------------------------------------------------------------
FAILED_REPOS=()
for repo in "${REPOS[@]}"; do
  slug="$(basename "${repo}")"
  transcript_file="${OUT_DIR}/${slug}.transcript.jsonl"
  timing_file="${OUT_DIR}/${slug}.timing.txt"

  # Refuse to clobber. If the human wants to re-run, they must move/delete
  # the prior artifact deliberately. This protects a captured baseline.
  if [[ -e "${transcript_file}" ]] || [[ -e "${timing_file}" ]]; then
    die "refusing to overwrite existing baseline artifact(s) for ${slug}. Move or remove ${transcript_file} and/or ${timing_file} before re-running."
  fi

  printf '\n--- repo: %s ---\n' "${repo}"
  printf 'transcript -> %s\n' "${transcript_file}"
  printf 'timing     -> %s\n' "${timing_file}"

  # /usr/bin/time -l is the macOS BSD flavor: -l adds the resource summary
  # block (RSS etc.) to stderr. -o writes that block to a file. We send the
  # codex transcript to stdout, which we tee to transcript_file.
  #
  # We use `set +e` around the codex call so a non-zero exit from codex
  # (which can happen on transient model errors) does not abort the whole
  # baseline run — we collect the failure and surface it at the end.
  set +e
  /usr/bin/time -l -o "${timing_file}" \
    codex exec \
      --skip-git-repo-check \
      --cwd "${repo}" \
      "${PROMPT_TEXT}" \
    > "${transcript_file}" 2>&1
  codex_rc=$?
  set -e

  # Sanity: both files must exist and be non-empty per Gate 1.4 pass condition.
  if [[ ! -s "${transcript_file}" ]] || [[ ! -s "${timing_file}" ]]; then
    FAILED_REPOS+=("${slug} (transcript or timing empty; codex rc=${codex_rc})")
    continue
  fi

  if [[ "${codex_rc}" -ne 0 ]]; then
    # Non-zero codex exit but artifacts present — record it but keep going.
    # The human reviews failed runs against the transcript content.
    FAILED_REPOS+=("${slug} (codex exit ${codex_rc}; transcript captured for review)")
  fi
done

# -----------------------------------------------------------------------------
# Final accounting.
# -----------------------------------------------------------------------------
printf '\n=== baseline_cold_start.sh summary ===\n'
printf 'repos requested: %d\n' "${#REPOS[@]}"
printf 'output dir:      %s\n' "${OUT_DIR}"

if [[ "${#FAILED_REPOS[@]}" -gt 0 ]]; then
  printf 'failures (%d):\n' "${#FAILED_REPOS[@]}"
  for f in "${FAILED_REPOS[@]}"; do
    printf '  - %s\n' "${f}"
  done
  printf '\nGate 1.4 cannot pass with failures present. Review the transcripts and re-run individually if appropriate.\n'
  exit 1
fi

printf 'all repos produced non-empty transcripts and timing files.\n'
printf 'next: validate against Gate 1.4 in docs/_validation_gates.md.\n'
exit 0
