"""Regex registry for parsing Codex CLI transcripts.

Feeds these validation gates from ``docs/_validation_gates.md``:
    * Gate 4.5 — Codex CLI actually invokes ``cam_recall`` in a recall-shaped task
    * Gate 5.2 — Rescue ladder activates after the 2nd consecutive failure
    * Gate 5.3 — Rescue ladder does not over-trigger on a 1st failure
    * Gate 6.3 — ``outcome_log`` skill writes after every verified step
    * Gate 9.x — End-to-end behavioural gates (provenance, learning, cold-start, rescue)

Every regex in this module is **version-tied** to the Codex CLI version pinned
in ``baselines/manifest.json``. The Codex CLI's transcript event format is not
a stable public contract; a CLI upgrade may rewrite tool-call markers,
re-order JSON fields, or rename event kinds. If the pinned version changes,
every regex below must be re-validated against fresh real transcripts before
any gate that depends on it is trusted.

This module does NOT mock, stub, or simulate transcript content. The parser
operates on real ``.transcript.jsonl`` files produced by
``tools/baseline_cold_start.sh`` and by Codex sessions under Phase 4+ gates.

Usage
-----
As a library::

    from tools.codex_trace_patterns import parse_transcript
    summary = parse_transcript(Path("baselines/cold_start/<slug>.transcript.jsonl"))

As a CLI::

    python -m tools.codex_trace_patterns <path-to-transcript>

The CLI form prints the parsed structure as JSON to stdout so humans can audit
the parse on real data.

Falsifier
---------
A passing parse on a synthetic string proves nothing. The ``__main__`` entry
point intentionally takes a real file path; it does not accept inline text.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Version pin loader.
# ---------------------------------------------------------------------------
# The Codex CLI version that these patterns were written against is read from
# ``baselines/manifest.json`` at import time. If the manifest is missing the
# import raises — that is intentional: any consumer of this module must be
# operating inside a workspace where the baseline manifest has been pinned.
#
# Rationale: ``_validation_gates.md`` Gate 4.5 explicitly says the regex is
# "tuned to the Codex CLI trace format pinned in Gate 1.2". This module is
# the single place that contract lives; it must point at the same manifest.
# ---------------------------------------------------------------------------

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "baselines" / "manifest.json"


def _load_pinned_cli_version() -> str:
    if not _MANIFEST_PATH.is_file():
        raise RuntimeError(
            f"codex_trace_patterns: baselines/manifest.json not found at {_MANIFEST_PATH}. "
            "The trace-pattern regex registry is version-tied; populate the manifest "
            "(Phase 1 Step 1.1) before importing this module."
        )
    data = json.loads(_MANIFEST_PATH.read_text())
    version = data.get("codex_cli_version", "")
    if not version:
        raise RuntimeError(
            "codex_trace_patterns: manifest.json is missing the 'codex_cli_version' field. "
            "Re-populate from baselines/manifest.json.template against the real machine."
        )
    return version


CODEX_CLI_VERSION: str = _load_pinned_cli_version()
"""The Codex CLI version these regex patterns are version-tied to.

Read once from ``baselines/manifest.json`` at module import. If a transcript
file declares a different CLI version in its header, ``parse_transcript``
raises ``RuntimeError`` rather than silently parsing under a mismatched
contract.
"""


# ---------------------------------------------------------------------------
# Pattern registry.
# ---------------------------------------------------------------------------
# Each pattern matches a well-known event in a Codex transcript. The Codex
# CLI emits two coarse transcript shapes: structured JSONL lines (one event
# per line) and free-text prose lines (model output). The regex below match
# *either*: they pick up the canonical JSONL field forms AND the prose
# rendering, because both appear in real transcripts depending on whether
# the user ran ``codex exec`` with or without ``--json``.
#
# Each pattern is compiled with re.IGNORECASE because the prose form varies
# in capitalization across CLI versions; the JSONL form is stable.
#
# When updating these patterns:
#   1. Update CODEX_CLI_VERSION in baselines/manifest.json first (via the
#      template flow), so import-time check tracks the new version.
#   2. Re-validate every gate that consumes these patterns against fresh
#      real transcripts.
# ---------------------------------------------------------------------------

TOOL_CALL_PATTERN: re.Pattern[str] = re.compile(
    # Matches either a JSONL-style event line:
    #     {"event":"tool_call","name":"cam_recall", ...}
    # or a prose rendering:
    #     "tool_call: cam_recall(query=...)"
    #     "invoking cam_recall"
    # The capture group `name` is the tool name (e.g., cam_recall).
    r'(?:"event"\s*:\s*"tool_call"[^{}]*"name"\s*:\s*"(?P<name>[A-Za-z_][A-Za-z0-9_]*)"'
    r'|\btool_call\s*:\s*(?P<name_prose>[A-Za-z_][A-Za-z0-9_]*)'
    r'|\binvoking\s+(?P<name_invoke>[A-Za-z_][A-Za-z0-9_]*)\b)',
    re.IGNORECASE,
)
"""Matches a Codex tool-call event.

Captures (in named groups, only one will be non-None per match):
    name        — from a JSONL "tool_call" event
    name_prose  — from a prose ``tool_call: <name>`` line
    name_invoke — from a prose ``invoking <name>`` line
"""

SKILL_ACTIVATE_PATTERN: re.Pattern[str] = re.compile(
    # JSONL: {"event":"skill_activate","name":"rescue_ladder"}
    # Prose: "skill_activate: rescue_ladder" or "activating skill rescue_ladder"
    r'(?:"event"\s*:\s*"skill_activate"[^{}]*"name"\s*:\s*"(?P<name>[A-Za-z_][A-Za-z0-9_\-]*)"'
    r'|\bskill_activate\s*:\s*(?P<name_prose>[A-Za-z_][A-Za-z0-9_\-]*)'
    r'|\bactivating\s+skill\s+(?P<name_activating>[A-Za-z_][A-Za-z0-9_\-]*)\b)',
    re.IGNORECASE,
)
"""Matches a Codex skill-activation event (e.g., ``rescue_ladder`` firing)."""

USER_ASKED_FOR_HELP_PATTERN: re.Pattern[str] = re.compile(
    # An escalation to the human user. Multiple surface forms; we accept
    # any of them so a CLI version bump that renames "user_asked_for_help"
    # to "ask_user" does not silently break Gate 9.5.
    r'(?:"event"\s*:\s*"user_asked_for_help"'
    r'|\buser_asked_for_help\b'
    r'|\baskUser\b'
    r'|\bask_user\b'
    r'|\bescalat(?:e|ed|ing)\s+to\s+user\b)',
    re.IGNORECASE,
)
"""Matches a Codex escalation event (Codex stopped and asked the user)."""

VERIFICATION_FAILURE_PATTERN: re.Pattern[str] = re.compile(
    # JSONL: {"event":"verification","result":"fail"} or {"result":"red"}
    # Prose: "verification failed", "tests failed", "build failed"
    # Gate 5.2 / 5.3 rely on counting these per turn.
    r'(?:"event"\s*:\s*"verification"[^{}]*"result"\s*:\s*"(?:fail(?:ed)?|red)"'
    r'|"result"\s*:\s*"(?:fail(?:ed)?|red)"'
    r'|\bverification\s+failed\b'
    r'|\btests?\s+failed\b'
    r'|\bbuild\s+failed\b)',
    re.IGNORECASE,
)
"""Matches a verification / test / build failure event."""

# Header sentinel: real Codex transcripts (JSONL form) begin with or contain
# a metadata event that records the CLI version. We use the same JSON shape
# the CLI emits for ``codex --version`` and for its session header.
_HEADER_VERSION_PATTERN: re.Pattern[str] = re.compile(
    r'"codex_(?:cli_)?version"\s*:\s*"(?P<version>[^"]+)"',
)


# ---------------------------------------------------------------------------
# Parse output.
# ---------------------------------------------------------------------------


@dataclass
class TraceEvent:
    """One classified event found in a transcript."""

    kind: str
    """One of: tool_call, skill_activate, user_asked_for_help, verification_failure."""

    name: str | None
    """For tool_call / skill_activate, the tool or skill name. None otherwise."""

    line_number: int
    """1-based line number in the source transcript file."""

    raw: str
    """The raw transcript line (trimmed). Useful for human audit when a gate fails."""


@dataclass
class TranscriptSummary:
    """Aggregate parse result for a single transcript file."""

    path: str
    line_count: int
    declared_cli_version: str | None
    events: list[TraceEvent] = field(default_factory=list)
    tool_call_counts: dict[str, int] = field(default_factory=dict)
    skill_activate_counts: dict[str, int] = field(default_factory=dict)
    user_asked_for_help_count: int = 0
    verification_failure_count: int = 0

    def to_jsonable(self) -> dict:
        """Convert to a plain dict suitable for ``json.dumps``."""
        return {
            "path": self.path,
            "line_count": self.line_count,
            "declared_cli_version": self.declared_cli_version,
            "pinned_cli_version": CODEX_CLI_VERSION,
            "tool_call_counts": self.tool_call_counts,
            "skill_activate_counts": self.skill_activate_counts,
            "user_asked_for_help_count": self.user_asked_for_help_count,
            "verification_failure_count": self.verification_failure_count,
            "events": [
                {
                    "kind": ev.kind,
                    "name": ev.name,
                    "line_number": ev.line_number,
                    "raw": ev.raw,
                }
                for ev in self.events
            ],
        }


def _extract_name(match: re.Match[str]) -> str | None:
    """Return the first non-None named capture, or None if all are None."""
    for key in ("name", "name_prose", "name_invoke", "name_activating"):
        try:
            value = match.group(key)
        except IndexError:
            value = None
        if value:
            return value
    return None


def _iter_classified_events(lines: Iterable[str]) -> Iterable[TraceEvent]:
    """Yield TraceEvent objects for every recognized line in ``lines``.

    A single line may legitimately contain multiple events (e.g., a JSONL
    line that wraps a tool_call and a verification field). We scan with
    ``finditer`` per pattern so co-occurring events are all recorded.
    """
    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        # tool_call
        for m in TOOL_CALL_PATTERN.finditer(line):
            yield TraceEvent(
                kind="tool_call",
                name=_extract_name(m),
                line_number=lineno,
                raw=line.strip(),
            )
        # skill_activate
        for m in SKILL_ACTIVATE_PATTERN.finditer(line):
            yield TraceEvent(
                kind="skill_activate",
                name=_extract_name(m),
                line_number=lineno,
                raw=line.strip(),
            )
        # user_asked_for_help — no name capture
        for _m in USER_ASKED_FOR_HELP_PATTERN.finditer(line):
            yield TraceEvent(
                kind="user_asked_for_help",
                name=None,
                line_number=lineno,
                raw=line.strip(),
            )
        # verification_failure — no name capture
        for _m in VERIFICATION_FAILURE_PATTERN.finditer(line):
            yield TraceEvent(
                kind="verification_failure",
                name=None,
                line_number=lineno,
                raw=line.strip(),
            )


def parse_transcript(path: Path) -> TranscriptSummary:
    """Parse a Codex transcript file and return a :class:`TranscriptSummary`.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist or is not a regular file.
    RuntimeError
        If the transcript declares a ``codex_cli_version`` that does not match
        the pinned ``CODEX_CLI_VERSION`` from ``baselines/manifest.json``.
        Version skew silently invalidates every behavioural gate that consumes
        the regex outputs, so we hard-fail here rather than producing
        misleading counts.
    """
    if not path.is_file():
        raise FileNotFoundError(f"transcript file not found: {path}")

    text = path.read_text(errors="replace")
    lines = text.splitlines()

    # Scan the first ~50 lines for a CLI version declaration. Codex header
    # events are at the top of the transcript; we cap the scan to avoid
    # treating a stray version mention in the middle of the conversation
    # as authoritative.
    declared_version: str | None = None
    for line in lines[:50]:
        m = _HEADER_VERSION_PATTERN.search(line)
        if m:
            declared_version = m.group("version")
            break

    if declared_version is not None and declared_version != CODEX_CLI_VERSION:
        # Allow partial match either direction (e.g., "0.42.1" vs "codex 0.42.1")
        if (
            declared_version not in CODEX_CLI_VERSION
            and CODEX_CLI_VERSION not in declared_version
        ):
            raise RuntimeError(
                f"codex_trace_patterns: transcript at {path} declares "
                f"codex_cli_version={declared_version!r} but the pinned "
                f"version in baselines/manifest.json is "
                f"{CODEX_CLI_VERSION!r}. Re-pin the manifest or re-capture "
                f"the transcript; do not silently proceed."
            )

    summary = TranscriptSummary(
        path=str(path),
        line_count=len(lines),
        declared_cli_version=declared_version,
    )

    for event in _iter_classified_events(lines):
        summary.events.append(event)
        if event.kind == "tool_call" and event.name:
            summary.tool_call_counts[event.name] = (
                summary.tool_call_counts.get(event.name, 0) + 1
            )
        elif event.kind == "skill_activate" and event.name:
            summary.skill_activate_counts[event.name] = (
                summary.skill_activate_counts.get(event.name, 0) + 1
            )
        elif event.kind == "user_asked_for_help":
            summary.user_asked_for_help_count += 1
        elif event.kind == "verification_failure":
            summary.verification_failure_count += 1

    return summary


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write(
            "usage: python -m tools.codex_trace_patterns <transcript.jsonl>\n"
        )
        return 2

    target = Path(argv[1]).expanduser().resolve()
    try:
        summary = parse_transcript(target)
    except (FileNotFoundError, RuntimeError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    json.dump(summary.to_jsonable(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct CLI use
    raise SystemExit(_main(sys.argv))
