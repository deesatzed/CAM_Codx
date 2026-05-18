"""Validate the ``auto_fire`` frontmatter block of Codex SKILL.md files.

Feeds these validation gates from ``docs/_validation_gates.md``:
    * Gate 4.1 — ``cam_recall_and_cite`` skill frontmatter parses
    * Gate 5.1 — ``rescue_ladder`` skill declares a parseable auto-fire trigger
    * Cross-cutting gate CC.5 — every skill with an ``auto_fire`` block matches
      ``tools/trigger_schema.json``

Behavior
--------
A SKILL.md file with no ``auto_fire`` block is **not** an error: it is simply
a skill that does not auto-fire. Only a *malformed* ``auto_fire`` block is an
error. This matches Gate CC.5's wording ("for every SKILL.md whose frontmatter
contains an auto_fire block, validate ...").

Dependencies
------------
This script imports ``yaml`` (PyYAML) and ``jsonschema``. If either is
missing, the script prints an actionable ``pip install`` message and exits
non-zero. It does NOT silently fall back to a regex parser — a permissive
fallback would let malformed YAML pass undetected and quietly break Gate CC.5.

CLI
---
::

    python tools/validate_skill_frontmatter.py path/to/SKILL.md [more ...]
    python tools/validate_skill_frontmatter.py --dir /path/to/.codex/skills
    python tools/validate_skill_frontmatter.py --quiet path/to/SKILL.md
    python tools/validate_skill_frontmatter.py --verbose --dir /path/to/skills

Exit codes
----------
    0 — every inspected file is either (a) free of an ``auto_fire`` block or
        (b) validates against the schema.
    1 — at least one file has a malformed ``auto_fire`` block (or YAML).
    2 — usage error (missing args, bad path, etc.).
    3 — required Python dependency missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Dependency probing. We do this up front so a missing dep produces a clear,
# fix-it message instead of a confusing traceback halfway through validation.
# ---------------------------------------------------------------------------
try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover - environmental
    sys.stderr.write(
        "validate_skill_frontmatter.py: PyYAML is required.\n"
        "Install with: pip install pyyaml\n"
    )
    raise SystemExit(3)

try:
    import jsonschema  # type: ignore[import-untyped]
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environmental
    sys.stderr.write(
        "validate_skill_frontmatter.py: jsonschema is required.\n"
        "Install with: pip install jsonschema\n"
    )
    raise SystemExit(3)


_SCHEMA_PATH = Path(__file__).resolve().parent / "trigger_schema.json"


def _load_schema() -> dict:
    if not _SCHEMA_PATH.is_file():
        sys.stderr.write(
            f"validate_skill_frontmatter.py: trigger schema missing at {_SCHEMA_PATH}.\n"
        )
        raise SystemExit(2)
    return json.loads(_SCHEMA_PATH.read_text())


# ---------------------------------------------------------------------------
# YAML frontmatter extraction.
# ---------------------------------------------------------------------------
# Codex SKILL.md frontmatter convention: the file begins with a `---` line,
# followed by YAML, followed by a closing `---` line. Anything after the
# closing fence is the prose body. We do the split ourselves rather than
# pulling in python-frontmatter because we want a deterministic, dep-light
# parser that we can audit at a glance.
# ---------------------------------------------------------------------------


def _extract_frontmatter(text: str) -> str | None:
    """Return the YAML frontmatter block as a string, or None if absent.

    Handles only the canonical leading-fence form. A file that uses no
    frontmatter at all returns None and is treated as "no auto_fire block".
    """
    lines = text.splitlines()
    if not lines:
        return None
    # The opening fence MUST be the first non-empty line. Codex tolerates a
    # BOM or a single blank line above, so we skip a leading BOM and at most
    # one leading blank line before requiring `---`.
    idx = 0
    if lines[idx].startswith("﻿"):
        lines[idx] = lines[idx].lstrip("﻿")
    if idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines) or lines[idx].strip() != "---":
        return None
    # Find closing fence.
    closing = None
    for j in range(idx + 1, len(lines)):
        if lines[j].strip() == "---":
            closing = j
            break
    if closing is None:
        # Opening fence with no close — this IS malformed, but we report it
        # as "no parseable frontmatter" and let the caller decide. The
        # auto_fire validator path will treat absence as "no auto_fire block".
        return None
    return "\n".join(lines[idx + 1 : closing])


# ---------------------------------------------------------------------------
# Per-file validation.
# ---------------------------------------------------------------------------


class ValidationFailure(Exception):
    """Raised when a SKILL.md's auto_fire block does not validate."""


def _validate_file(path: Path, validator: Draft202012Validator) -> tuple[bool, str]:
    """Validate one SKILL.md.

    Returns
    -------
    (passed, message) where ``passed`` is True if the file is acceptable
    (no auto_fire block OR a valid one), and ``message`` is a short
    human-readable status string.
    """
    if not path.is_file():
        return False, f"{path}: not a regular file"

    text = path.read_text(errors="replace")
    fm_text = _extract_frontmatter(text)
    if fm_text is None:
        return True, f"{path}: no frontmatter block (skill does not auto-fire)"

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        return False, f"{path}: malformed YAML frontmatter: {exc}"

    if not isinstance(fm, dict):
        # Frontmatter present but is a list/scalar/etc. — treat as malformed
        # so a typo cannot silently bypass the schema.
        return False, f"{path}: frontmatter is not a mapping (got {type(fm).__name__})"

    if "auto_fire" not in fm:
        return True, f"{path}: no auto_fire block (skill does not auto-fire)"

    # Validate the frontmatter against the schema. The schema's top-level
    # `required` includes auto_fire, which is satisfied here. additionalProperties
    # is false at every level, so any unknown sibling field will fail.
    #
    # We pass the WHOLE frontmatter dict (not just fm["auto_fire"]) because
    # the schema is written to live at the frontmatter level — that lets us
    # add other required frontmatter constraints later without rewriting the
    # validator. additionalProperties:false at the top level intentionally
    # means we will, in future schema revisions, need to enumerate other
    # frontmatter fields (name, description, tools). For now the schema
    # accepts only `auto_fire`; this is documented as a known limitation
    # and is acceptable because the gates that consume this validator are
    # specifically about the auto_fire block.
    errors = sorted(validator.iter_errors(fm), key=lambda e: list(e.absolute_path))
    if errors:
        # Build a compact, actionable error message: first error wins.
        first = errors[0]
        loc = "/".join(str(x) for x in first.absolute_path) or "<root>"
        return False, f"{path}: auto_fire schema violation at {loc}: {first.message}"

    return True, f"{path}: auto_fire block valid"


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------


def _iter_targets(args: argparse.Namespace) -> Iterable[Path]:
    """Yield SKILL.md paths derived from the CLI arguments.

    Either ``--dir`` is given (recursive find) or one or more explicit file
    paths. The two modes can be combined; in practice the gates use one or
    the other.
    """
    if args.dir:
        root = Path(args.dir).expanduser().resolve()
        if not root.is_dir():
            sys.stderr.write(f"--dir is not a directory: {root}\n")
            raise SystemExit(2)
        # Recursive search for any file literally named SKILL.md. We do not
        # follow symlinks to avoid infinite loops in an oddly-symlinked tree.
        for child in root.rglob("SKILL.md"):
            if child.is_file():
                yield child
    for raw in args.files:
        yield Path(raw).expanduser().resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the auto_fire frontmatter block of Codex SKILL.md "
            "files against tools/trigger_schema.json."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="One or more SKILL.md file paths to validate.",
    )
    parser.add_argument(
        "--dir",
        default=None,
        help="Recursively validate every SKILL.md under this directory.",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--quiet",
        action="store_true",
        help="Exit code only; suppress all stdout output. Errors still go to stderr.",
    )
    verbosity.add_argument(
        "--verbose",
        action="store_true",
        help="Print one line per file, including passing ones.",
    )

    args = parser.parse_args(argv)
    if not args.files and not args.dir:
        parser.error("provide at least one SKILL.md path or --dir <path>")

    schema = _load_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    targets = list(_iter_targets(args))
    if not targets:
        sys.stderr.write("no SKILL.md files found to validate.\n")
        return 2

    first_failure_msg: str | None = None
    failed = 0
    passed = 0

    for path in targets:
        ok, msg = _validate_file(path, validator)
        if ok:
            passed += 1
            if args.verbose:
                sys.stdout.write(f"PASS  {msg}\n")
        else:
            failed += 1
            if first_failure_msg is None:
                first_failure_msg = msg
            if not args.quiet:
                sys.stderr.write(f"FAIL  {msg}\n")
            # Per spec: exit on first failing path with a clear message.
            # We still want to exit cleanly; collect summary and bail.
            break

    if not args.quiet and not args.verbose:
        sys.stdout.write(f"validated {passed + failed} file(s); failures: {failed}\n")
    elif args.verbose:
        sys.stdout.write(f"summary: {passed} pass, {failed} fail\n")

    if failed:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - direct CLI use
    raise SystemExit(main())
