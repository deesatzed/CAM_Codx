"""Read bounded WIP evidence and derive source-linked opportunity needs.

This module deliberately stops at target inspection and need description.  It
does not run the target, contact a provider, inspect CAM's database, or propose
implementation steps.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Literal
import unicodedata


VerificationStatus = Literal["not_run"]
NeedCategory = Literal["blocker", "risk", "next_action", "open_question"]

MAX_HANDOFF_BYTES = 256 * 1024
MAX_INSPECTED_FILES = 512
MAX_GAPS = 128
MAX_DIRTY_ENTRIES = 256
MAX_BULLET_CHARS = 2_000
MAX_SECTION_BULLETS = 128

TRUTH_FILE_NAMES = (
    "GOAL.md",
    "STANDARDS.md",
    "IMPLEMENT.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "TASK_QUEUE.md",
    "AGENTS.md",
)

_SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        ".benchmarks",
        "node_modules",
        "vendor",
        "dependencies",
        "deps",
        "build",
        "dist",
        "generated_candidates",
        "generated_evidence",
        "hidden_evaluators",
        "run_artifacts",
    }
)

_TEXT_SUFFIXES = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".kt",
        ".md",
        ".py",
        ".rs",
        ".sh",
        ".swift",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
)

_GAP_PATTERN = re.compile(r"\b(?:TODO|FIXME|NotImplemented(?:Error)?)\b", re.IGNORECASE)
_DATED_HANDOFF_PATTERN = re.compile(
    r"^handoff[^/]*?(?P<date>\d{4}-\d{2}-\d{2})[^/]*\.md$",
    re.IGNORECASE,
)
_ATX_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_PLAIN_HEADING_PATTERN = re.compile(r"^\s*([A-Za-z][A-Za-z /&-]{1,48}):\s*$")
_BULLET_PATTERN = re.compile(r"^\s*(?:[-*+]\s+|\d{1,3}[.)]\s+)(.+?)\s*$")
_PRIORITY_PATTERN = re.compile(
    r"^\s*(?:\[\s*(P[0-2])\s*\]|\*{0,2}(P[0-2])\*{0,2}\s*:)\s*",
    re.IGNORECASE,
)
_CLAIM_PATTERN = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*{0,2})"
    r"(?P<kind>branch|revision|head|commit)(?:\*{0,2})\s*:\s*"
    r"(?:`)?(?P<value>[^`\s]+)(?:`)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_SECTION_CATEGORIES: dict[str, NeedCategory] = {
    "blocker": "blocker",
    "blockers": "blocker",
    "risk": "risk",
    "risks": "risk",
    "unknown": "risk",
    "unknowns": "risk",
    "risk unknown": "risk",
    "risk unknowns": "risk",
    "risks unknown": "risk",
    "risks unknowns": "risk",
    "next action": "next_action",
    "next actions": "next_action",
    "open question": "open_question",
    "open questions": "open_question",
}
_CATEGORY_ORDER: dict[NeedCategory, int] = {
    "blocker": 0,
    "risk": 1,
    "next_action": 2,
    "open_question": 3,
}
_CATEGORY_LABELS: dict[NeedCategory, str] = {
    "blocker": "blocker",
    "risk": "risk or unknown",
    "next_action": "next action",
    "open_question": "open question",
}


class OpportunityBriefError(ValueError):
    """Raised when bounded WIP evidence cannot support need extraction."""


@dataclass(frozen=True)
class HandoffEvidence:
    """Exact bytes-derived evidence selected as the current handoff."""

    relative_path: str
    sha256: str
    text: str


@dataclass(frozen=True)
class WipSnapshot:
    """Read-only snapshot of bounded, locally visible target evidence."""

    target_path: Path
    target_revision: str | None
    target_repo_id: str
    branch: str | None
    dirty_entries: tuple[str, ...]
    handoff: HandoffEvidence | None
    truth_files: tuple[str, ...]
    visible_gaps: tuple[str, ...]
    conflicts: tuple[str, ...]
    verification_status: VerificationStatus


@dataclass(frozen=True)
class NeedTheme:
    """A source-linked need theme, never an implementation plan."""

    need_id: str
    category: NeedCategory
    problem: str
    desired_improvement: str
    existing_evidence: str
    gap: str
    query_text: str
    handoff_span: str
    implementation_steps: tuple[()] = ()


@dataclass(frozen=True)
class _Candidate:
    category: NeedCategory
    priority: int
    source_order: int
    handoff_span: str
    problem: str
    normalized_problem: str


def inspect_wip_repository(target_path: Path) -> WipSnapshot:
    """Inspect a local target without running it or writing to it.

    Inspection is bounded by file count, file size, gap count, and dirty-entry
    count.  Git optional locks are disabled for the fixed read-only commands.
    """

    target = Path(target_path).expanduser().resolve()
    if not target.is_dir():
        raise OpportunityBriefError("target path must be an existing directory")

    truth_files = tuple(name for name in TRUTH_FILE_NAMES if (target / name).is_file())
    handoff = _read_selected_handoff(target, truth_files)
    revision = _git_value(target, "rev-parse", "--verify", "HEAD")
    branch = _git_value(target, "symbolic-ref", "--quiet", "--short", "HEAD")
    dirty_entries = _read_dirty_entries(target)
    visible_gaps = _read_visible_gaps(target)
    conflicts = _find_checkout_conflicts(handoff, revision=revision, branch=branch)

    return WipSnapshot(
        target_path=target,
        target_revision=revision,
        target_repo_id=_target_repo_id(target),
        branch=branch,
        dirty_entries=dirty_entries,
        handoff=handoff,
        truth_files=truth_files,
        visible_gaps=visible_gaps,
        conflicts=conflicts,
        verification_status="not_run",
    )


def extract_need_themes(
    snapshot: WipSnapshot,
    *,
    minimum: int = 3,
    maximum: int = 7,
) -> tuple[NeedTheme, ...]:
    """Extract three to seven ranked needs from allowed handoff sections."""

    _validate_need_bounds(minimum, maximum)
    if snapshot.handoff is None:
        raise OpportunityBriefError("a handoff or truth file is required to extract needs")

    candidates = _parse_candidates(snapshot.handoff.text)
    ranked = sorted(
        candidates,
        key=lambda item: (item.priority, _CATEGORY_ORDER[item.category], item.source_order),
    )
    selected: list[_Candidate] = []
    seen: set[str] = set()
    for candidate in ranked:
        if candidate.normalized_problem in seen:
            continue
        seen.add(candidate.normalized_problem)
        selected.append(candidate)
        if len(selected) == maximum:
            break

    if len(selected) < minimum:
        raise OpportunityBriefError(
            f"handoff must contain at least {minimum} unique needs in allowed sections"
        )
    return tuple(_to_need_theme(candidate) for candidate in selected)


def _read_selected_handoff(
    target: Path,
    truth_files: tuple[str, ...],
) -> HandoffEvidence | None:
    latest = target / "HANDOFF_LATEST.md"
    if latest.is_file() and not latest.is_symlink():
        return _read_evidence(target, latest)

    dated: list[tuple[str, str, Path]] = []
    try:
        children = sorted(target.iterdir(), key=lambda path: path.name.casefold())
    except OSError as error:
        raise OpportunityBriefError("target directory could not be read") from error
    for path in children[:MAX_INSPECTED_FILES]:
        if not path.is_file() or path.is_symlink():
            continue
        match = _DATED_HANDOFF_PATTERN.fullmatch(path.name)
        if match:
            dated.append((match.group("date"), path.name.casefold(), path))
    if dated:
        return _read_evidence(target, max(dated)[2])

    for name in truth_files:
        path = target / name
        if not path.is_symlink():
            return _read_evidence(target, path)
    return None


def _read_evidence(target: Path, path: Path) -> HandoffEvidence:
    try:
        stat_result = path.stat()
        if stat_result.st_size > MAX_HANDOFF_BYTES:
            raise OpportunityBriefError("selected handoff exceeds the bounded size")
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except OpportunityBriefError:
        raise
    except (OSError, UnicodeError) as error:
        raise OpportunityBriefError("selected handoff must be readable UTF-8 text") from error
    if len(raw) > MAX_HANDOFF_BYTES:
        raise OpportunityBriefError("selected handoff exceeds the bounded size")
    return HandoffEvidence(
        relative_path=path.relative_to(target).as_posix(),
        sha256=hashlib.sha256(raw).hexdigest(),
        text=text,
    )


def _git_value(target: Path, *arguments: str) -> str | None:
    completed = _run_git(target, *arguments)
    if completed is None:
        return None
    value = completed.stdout.strip()
    return value or None


def _run_git(target: Path, *arguments: str) -> subprocess.CompletedProcess[str] | None:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(target), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed if completed.returncode == 0 else None


def _read_dirty_entries(target: Path) -> tuple[str, ...]:
    completed = _run_git(
        target,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if completed is None:
        return ()

    entries: list[str] = []
    for raw_line in completed.stdout.splitlines():
        if len(raw_line) < 4:
            continue
        status = raw_line[:2]
        raw_path = raw_line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.rsplit(" -> ", 1)[1]
        relative_path = _unquote_git_path(raw_path)
        if _path_is_skipped(relative_path):
            continue
        entries.append(f"{status} {relative_path}")
        if len(entries) == MAX_DIRTY_ENTRIES:
            break
    return tuple(entries)


def _unquote_git_path(value: str) -> str:
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        try:
            return bytes(value[1:-1], "utf-8").decode("unicode_escape")
        except UnicodeError:
            return value[1:-1]
    return value


def _read_visible_gaps(target: Path) -> tuple[str, ...]:
    gaps: list[str] = []
    inspected = 0
    for root, directories, files in os.walk(target, topdown=True, followlinks=False):
        root_path = Path(root)
        directories[:] = sorted(
            (
                name
                for name in directories
                if not _path_is_skipped((root_path / name).relative_to(target).as_posix())
                and not (root_path / name).is_symlink()
            ),
            key=str.casefold,
        )
        for filename in sorted(files, key=str.casefold):
            path = root_path / filename
            relative = path.relative_to(target).as_posix()
            if _path_is_skipped(relative) or path.is_symlink():
                continue
            if path.suffix.casefold() not in _TEXT_SUFFIXES:
                continue
            inspected += 1
            if inspected > MAX_INSPECTED_FILES:
                return tuple(gaps)
            try:
                if path.stat().st_size > MAX_HANDOFF_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                match = _GAP_PATTERN.search(line)
                if not match:
                    continue
                excerpt = " ".join(line.strip().split())[:240]
                gaps.append(f"{relative}:{line_number}: {excerpt}")
                if len(gaps) == MAX_GAPS:
                    return tuple(gaps)
    return tuple(gaps)


def _path_is_skipped(relative_path: str) -> bool:
    for part in PurePosixPath(relative_path).parts:
        normalized = re.sub(r"[\s-]+", "_", part.casefold())
        if normalized in _SKIPPED_DIRECTORY_NAMES:
            return True
    return False


def _target_repo_id(target: Path) -> str:
    name = unicodedata.normalize("NFKC", target.name).casefold()
    slug = re.sub(r"[^a-z0-9._-]+", "-", name).strip("-.")
    if not slug:
        slug = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:16]
    return f"local:{slug}"


def _find_checkout_conflicts(
    handoff: HandoffEvidence | None,
    *,
    revision: str | None,
    branch: str | None,
) -> tuple[str, ...]:
    if handoff is None:
        return ()
    conflicts: list[str] = []
    for match in _CLAIM_PATTERN.finditer(handoff.text[:MAX_HANDOFF_BYTES]):
        kind = match.group("kind").casefold()
        claimed = match.group("value")
        if kind == "branch":
            if branch is not None and claimed != branch:
                conflicts.append(
                    f"handoff branch {claimed!r} conflicts with live branch {branch!r}"
                )
            continue
        if revision is not None and not revision.casefold().startswith(claimed.casefold()):
            conflicts.append(
                f"handoff revision {claimed!r} conflicts with live revision {revision!r}"
            )
    return tuple(dict.fromkeys(conflicts))


def _validate_need_bounds(minimum: int, maximum: int) -> None:
    if (
        isinstance(minimum, bool)
        or isinstance(maximum, bool)
        or not isinstance(minimum, int)
        or not isinstance(maximum, int)
        or minimum < 3
        or maximum > 7
        or minimum > maximum
    ):
        raise OpportunityBriefError("need bounds must satisfy 3 <= minimum <= maximum <= 7")


def _parse_candidates(text: str) -> tuple[_Candidate, ...]:
    current_category: NeedCategory | None = None
    candidates: list[_Candidate] = []
    source_order = 0
    for line in text.splitlines():
        heading = _heading_text(line)
        if heading is not None:
            current_category = _category_for_heading(heading)
            continue
        if current_category is None:
            continue
        bullet = _BULLET_PATTERN.match(line)
        if bullet is None:
            continue
        handoff_span = bullet.group(1).strip()
        if not handoff_span or len(handoff_span) > MAX_BULLET_CHARS:
            continue
        source_order += 1
        if source_order > MAX_SECTION_BULLETS:
            break
        priority, problem = _strip_priority(handoff_span)
        normalized = _normalize_span(problem)
        if not normalized:
            continue
        candidates.append(
            _Candidate(
                category=current_category,
                priority=priority,
                source_order=source_order,
                handoff_span=handoff_span,
                problem=problem,
                normalized_problem=normalized,
            )
        )
    return tuple(candidates)


def _heading_text(line: str) -> str | None:
    atx = _ATX_HEADING_PATTERN.match(line)
    if atx:
        return atx.group(1)
    plain = _PLAIN_HEADING_PATTERN.match(line)
    if plain:
        return plain.group(1)
    return None


def _category_for_heading(heading: str) -> NeedCategory | None:
    normalized = unicodedata.normalize("NFKC", heading).casefold()
    normalized = normalized.replace("&", " ").replace("/", " ")
    normalized = " ".join(re.sub(r"[^a-z ]+", " ", normalized).split())
    return _SECTION_CATEGORIES.get(normalized)


def _strip_priority(handoff_span: str) -> tuple[int, str]:
    match = _PRIORITY_PATTERN.match(handoff_span)
    if match is None:
        return 3, handoff_span.strip()
    label = (match.group(1) or match.group(2)).casefold()
    problem = handoff_span[match.end() :].strip()
    return int(label[1]), problem


def _normalize_span(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized)
    return " ".join(normalized.split())


def _to_need_theme(candidate: _Candidate) -> NeedTheme:
    label = _CATEGORY_LABELS[candidate.category]
    identity_input = f"{candidate.category}\0{candidate.normalized_problem}".encode("utf-8")
    need_id = f"need_{hashlib.sha256(identity_input).hexdigest()[:24]}"
    return NeedTheme(
        need_id=need_id,
        category=candidate.category,
        problem=candidate.problem,
        desired_improvement=(
            f"Resolve the recorded {label} with an auditable, transferable improvement."
        ),
        existing_evidence=(
            f"The selected handoff records this {label}: {candidate.handoff_span}"
        ),
        gap="Independent source-grounded evidence for a transferable mechanism is not attached.",
        query_text=(
            f"{candidate.problem} source-grounded evidence transferable mechanism verification"
        ),
        handoff_span=candidate.handoff_span,
    )


__all__ = [
    "HandoffEvidence",
    "NeedTheme",
    "OpportunityBriefError",
    "WipSnapshot",
    "extract_need_themes",
    "inspect_wip_repository",
]
