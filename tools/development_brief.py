#!/usr/bin/env python3
"""Typed, read-only presentation contract for CAM_Codx Development Briefs.

This module deliberately begins with pure data validation and Markdown
rendering.  Target inspection and CAM retrieval are added in later plan tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
