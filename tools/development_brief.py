#!/usr/bin/env python3
"""Typed, read-only presentation contract for CAM_Codx Development Briefs.

This module deliberately begins with pure data validation and Markdown
rendering.  Target inspection and CAM retrieval are added in later plan tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import subprocess


class BriefValidationError(ValueError):
    """Raised when a Development Brief payload is incomplete or ambiguous."""


class EvidenceClass(str, Enum):
    DIRECT_PRECEDENT = "direct_precedent"
    TRANSFERABLE_ANALOGY = "transferable_analogy"
    NEW_HYPOTHESIS = "new_hypothesis"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_EVIDENCE_LABELS = {
    EvidenceClass.DIRECT_PRECEDENT: "Direct precedent",
    EvidenceClass.TRANSFERABLE_ANALOGY: "Transferable analogy",
    EvidenceClass.NEW_HYPOTHESIS: "New hypothesis",
}

_TRUTH_FILES = (
    "GOAL.md",
    "STANDARDS.md",
    "IMPLEMENT.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "TASK_QUEUE.md",
    "AGENTS.md",
)
_GAP_MARKERS = ("TODO", "FIXME", "NotImplemented")
_SKIPPED_DIRECTORIES = {".git", ".venv", "node_modules", "vendor", "build", "dist", ".direnv"}
_SENSITIVE_NAME_MARKERS = (".env", "secret", "credential", "private", "token", "key")
_MAX_INSPECTED_FILES = 200
_MAX_FILE_BYTES = 256 * 1024


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BriefValidationError(f"{field_name} must be non-empty")
    return value.strip()


@dataclass(frozen=True)
class BriefRequest:
    mode: str
    task_text: str

    def __post_init__(self) -> None:
        if self.mode not in {"new", "continue-rescue"}:
            raise BriefValidationError("mode must be 'new' or 'continue-rescue'")
        object.__setattr__(self, "task_text", _required_text(self.task_text, "task_text"))


@dataclass(frozen=True)
class EvidenceItem:
    evidence_class: EvidenceClass
    title: str
    source_id: str
    source_kind: str
    why_it_applies: str
    confidence: Confidence
    limitation: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_class, EvidenceClass):
            raise BriefValidationError("evidence class must be a known EvidenceClass")
        if not isinstance(self.confidence, Confidence):
            raise BriefValidationError("confidence must be a known Confidence")
        for field_name in (
            "title",
            "source_id",
            "source_kind",
            "why_it_applies",
            "limitation",
        ):
            object.__setattr__(self, field_name, _required_text(getattr(self, field_name), field_name))


@dataclass(frozen=True)
class TargetEvidence:
    category: str
    summary: str
    source_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", _required_text(self.category, "category"))
        object.__setattr__(self, "summary", _required_text(self.summary, "summary"))
        if self.source_path is not None:
            object.__setattr__(self, "source_path", _required_text(self.source_path, "source_path"))


@dataclass(frozen=True)
class NextStep:
    kind: str
    summary: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _required_text(self.kind, "next-step kind"))
        object.__setattr__(self, "summary", _required_text(self.summary, "next-step summary"))


@dataclass(frozen=True)
class TargetInspection:
    """Facts collected from one named target without running its code."""

    target_path: Path
    is_git_repository: bool
    branch: str | None
    read_truth_files: tuple[str, ...]
    missing_truth_files: tuple[str, ...]
    dirty_entries: tuple[str, ...]
    visible_gaps: tuple[str, ...]
    risks: tuple[str, ...]
    verification_status: str

    def __post_init__(self) -> None:
        if self.verification_status != "not_run":
            raise BriefValidationError("verification_status must be 'not_run' for read-only inspection")


@dataclass(frozen=True)
class ContinueRescueAdvice:
    """An explicitly limited recommendation derived from target facts."""

    action: str
    reasons: tuple[str, ...]
    limitation: str
    recommended_next_step: NextStep

    def __post_init__(self) -> None:
        if self.action not in {"continue", "mitigate", "re-develop"}:
            raise BriefValidationError("continue/rescue action is invalid")
        if not self.reasons:
            raise BriefValidationError("continue/rescue advice requires reasons")
        object.__setattr__(self, "limitation", _required_text(self.limitation, "advice limitation"))


@dataclass(frozen=True)
class DevelopmentBrief:
    request: BriefRequest
    target_evidence: tuple[TargetEvidence, ...]
    evidence_items: tuple[EvidenceItem, ...]
    recommendation: str
    recommended_next_step: NextStep
    optional_next_steps: tuple[NextStep, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.request, BriefRequest):
            raise BriefValidationError("request must be a BriefRequest")
        if not isinstance(self.recommended_next_step, NextStep):
            raise BriefValidationError("recommended_next_step must be a NextStep")
        object.__setattr__(self, "recommendation", _required_text(self.recommendation, "recommendation"))
        for item in self.target_evidence:
            if not isinstance(item, TargetEvidence):
                raise BriefValidationError("target_evidence must contain TargetEvidence")
        for item in self.evidence_items:
            if not isinstance(item, EvidenceItem):
                raise BriefValidationError("evidence_items must contain EvidenceItem")
        for item in self.optional_next_steps:
            if not isinstance(item, NextStep):
                raise BriefValidationError("optional_next_steps must contain NextStep")
        cleaned_limits = tuple(_required_text(item, "limitation") for item in self.limitations)
        object.__setattr__(self, "limitations", cleaned_limits)


def _is_sensitive_path(path: Path) -> bool:
    name = path.name.lower()
    return any(marker in name for marker in _SENSITIVE_NAME_MARKERS)


def _read_limited_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _git_status_read_only(target: Path) -> tuple[bool, str | None, tuple[str, ...]]:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            ["git", "-C", str(target), "status", "--short", "--branch", "--untracked-files=all"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, None, ()
    if completed.returncode != 0:
        return False, None, ()
    lines = tuple(line for line in completed.stdout.splitlines() if line.strip())
    branch = lines[0][3:].strip() if lines and lines[0].startswith("## ") else None
    dirty = tuple(line for line in lines if not line.startswith("## "))
    return True, branch, dirty


def _visible_gap_markers(target: Path) -> tuple[str, ...]:
    findings: list[str] = []
    inspected = 0
    for path in sorted(target.rglob("*")):
        if inspected >= _MAX_INSPECTED_FILES:
            break
        if not path.is_file() or any(part in _SKIPPED_DIRECTORIES for part in path.parts):
            continue
        if _is_sensitive_path(path):
            continue
        text = _read_limited_text(path)
        if text is None or "\x00" in text:
            continue
        inspected += 1
        relative_path = path.relative_to(target)
        for line_number, line in enumerate(text.splitlines(), start=1):
            for marker in _GAP_MARKERS:
                if marker in line:
                    findings.append(f"{relative_path}:{line_number}: {marker}")
    return tuple(findings)


def inspect_target_read_only(target_path: Path) -> TargetInspection:
    """Inspect a single, explicitly named repository without executing it."""

    target = Path(target_path).expanduser().resolve()
    if not target.is_dir():
        raise BriefValidationError(f"target repository is not a directory: {target}")

    read_truth_files: list[str] = []
    missing_truth_files: list[str] = []
    for name in _TRUTH_FILES:
        candidate = target / name
        if candidate.is_file() and _read_limited_text(candidate) is not None:
            read_truth_files.append(name)
        else:
            missing_truth_files.append(name)

    is_git_repository, branch, dirty_entries = _git_status_read_only(target)
    risks: list[str] = []
    if not is_git_repository:
        risks.append("target is not a Git repository")
    if not read_truth_files:
        risks.append("target has no readable repository truth files")

    return TargetInspection(
        target_path=target,
        is_git_repository=is_git_repository,
        branch=branch,
        read_truth_files=tuple(read_truth_files),
        missing_truth_files=tuple(missing_truth_files),
        dirty_entries=dirty_entries,
        visible_gaps=_visible_gap_markers(target),
        risks=tuple(risks),
        verification_status="not_run",
    )


def recommend_continue_rescue(
    inspection: TargetInspection,
    *,
    current_test_receipt: str | None = None,
) -> ContinueRescueAdvice:
    """Give advisory, deterministic continuation advice from observable facts."""

    if not inspection.is_git_repository or inspection.risks or len(inspection.missing_truth_files) >= 2:
        reasons = list(inspection.risks)
        if inspection.missing_truth_files:
            reasons.append("repository truth is missing or incomplete")
        return ContinueRescueAdvice(
            action="re-develop",
            reasons=tuple(reasons),
            limitation="This is advisory; a human must review whether re-development is proportionate.",
            recommended_next_step=NextStep(
                kind="prepare_redevelopment_plan",
                summary="Preserve useful evidence, then create a bounded re-development plan.",
            ),
        )

    if (
        current_test_receipt == "passed"
        and not inspection.dirty_entries
        and not inspection.visible_gaps
        and not inspection.missing_truth_files
    ):
        return ContinueRescueAdvice(
            action="continue",
            reasons=("current test receipt passed and no structural red flags were observed",),
            limitation="This does not prove product completeness or replace a focused change review.",
            recommended_next_step=NextStep(
                kind="continue_smallest_step",
                summary="Implement the smallest planned increment and run its named verification.",
            ),
        )

    reasons: list[str] = []
    if inspection.dirty_entries:
        reasons.append("dirty worktree entries need review before further changes")
    if inspection.visible_gaps:
        reasons.append("visible gap markers need bounded investigation")
    if current_test_receipt != "passed":
        reasons.append("current verification evidence is unavailable or not passing")
    if inspection.missing_truth_files:
        reasons.append("some repository truth files are absent")
    return ContinueRescueAdvice(
        action="mitigate",
        reasons=tuple(reasons),
        limitation="The recommendation is advisory; confirm the named gap with focused verification.",
        recommended_next_step=NextStep(
            kind="prepare_mitigation_plan",
            summary="Choose one bounded gap, define its verification, and repair it before expanding scope.",
        ),
    )


def render_markdown(brief: DevelopmentBrief) -> str:
    """Render a concise Development Brief without performing any I/O."""

    lines = [
        "# Development Brief",
        "",
        f"**Mode:** {brief.request.mode}",
        f"**Task:** {brief.request.task_text}",
        "**Scope:** Named target plus existing CAM primary knowledge only; no mutation performed.",
        "",
        "## Target evidence",
    ]
    if brief.target_evidence:
        for item in brief.target_evidence:
            origin = f" (`{item.source_path}`)" if item.source_path else ""
            lines.append(f"- **{item.category}:** {item.summary}{origin}")
    else:
        lines.append("- No target evidence was collected.")

    lines.extend(["", "## Evidence"])
    if brief.evidence_items:
        for item in brief.evidence_items:
            lines.extend(
                [
                    f"### {_EVIDENCE_LABELS[item.evidence_class]}: {item.title}",
                    f"- Source: `{item.source_kind}:{item.source_id}`",
                    f"- Why this applies: {item.why_it_applies}",
                    f"- Confidence: {item.confidence.value}",
                    f"- Limitation: {item.limitation}",
                    "",
                ]
            )
    else:
        lines.append("- No CAM evidence retrieved.")

    lines.extend(
        [
            "",
            "## Recommendation",
            brief.recommendation,
            "",
            "## Recommended next step",
            f"- **{brief.recommended_next_step.kind}:** {brief.recommended_next_step.summary}",
            "",
            "## Limitations",
        ]
    )
    if brief.limitations:
        lines.extend(f"- {item}" for item in brief.limitations)
    else:
        lines.append("- No additional limitations recorded.")

    if brief.optional_next_steps:
        lines.extend(["", "## Optional explicit next steps"])
        lines.extend(f"- **{item.kind}:** {item.summary}" for item in brief.optional_next_steps)

    return "\n".join(lines).rstrip() + "\n"
